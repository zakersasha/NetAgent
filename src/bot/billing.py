from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from bot.device_presets import get_device_preset
from bot.plans import Plan as PlanView
from netagent_common.device_id import make_device_id
from netagent_common.vless_uri import build_vless_reality_uri
from netagent_db.models import Device, Payment, Plan, Subscription, User
from xray_client.client import XrayAgentClient, XrayAgentClientError


class DeviceLimitExceededError(ValueError):
    """User reached the device limit for their plan."""


class DeviceAlreadyExistsError(ValueError):
    """This device type is already registered for the user."""


class DeviceNotFoundError(ValueError):
    """Device not found for this user."""


class NoSubscriptionError(ValueError):
    """User has no active subscription."""


class BillingError(ValueError):
    """Generic billing error."""


class DeviceView:
    __slots__ = (
        "id",
        "slug",
        "emoji",
        "display_name",
        "xray_uuid",
        "xray_email",
        "connection_uri",
        "created_at",
    )

    def __init__(
        self,
        id: int,
        slug: str,
        emoji: str,
        display_name: str,
        xray_uuid: str,
        xray_email: str,
        connection_uri: str,
        created_at: datetime,
    ) -> None:
        self.id = id
        self.slug = slug
        self.emoji = emoji
        self.display_name = display_name
        self.xray_uuid = xray_uuid
        self.xray_email = xray_email
        self.connection_uri = connection_uri
        self.created_at = created_at


class SubscriptionView:
    __slots__ = ("telegram_id", "plan", "expires_at", "devices")

    def __init__(
        self,
        telegram_id: int,
        plan: PlanView,
        expires_at: datetime,
        devices: tuple[DeviceView, ...] = (),
    ) -> None:
        self.telegram_id = telegram_id
        self.plan = plan
        self.expires_at = expires_at
        self.devices = devices


class BillingClient:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        public_host: str,
        public_port: int = 443,
        timezone: str = "Europe/Moscow",
        reality_public_key: str = "",
        reality_sni: str = "www.wikipedia.org",
        reality_short_id: str = "6ba85179e30d4fc3",
        vless_flow: str = "xtls-rprx-vision",
        xray_agent: XrayAgentClient | None = None,
    ) -> None:
        self._session_factory = session_factory
        self.public_host = public_host
        self.public_port = public_port
        self.timezone = ZoneInfo(timezone)
        self.reality_public_key = reality_public_key.strip()
        self.reality_sni = reality_sni
        self.reality_short_id = reality_short_id
        self.vless_flow = vless_flow
        self._xray_agent = xray_agent

    def plans(self) -> tuple[PlanView, ...]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.sort_order)
            ).all()
            return tuple(self._plan_view(row) for row in rows)

    def get_subscription(self, telegram_id: int) -> SubscriptionView | None:
        with self._session_factory() as session:
            return self._load_subscription_view(session, telegram_id)

    def activate_mock_payment(self, telegram_id: int, plan_slug: str) -> SubscriptionView:
        with self._session_factory() as session:
            plan = session.scalar(select(Plan).where(Plan.slug == plan_slug, Plan.is_active.is_(True)))
            if not plan:
                raise BillingError(f"Unknown plan: {plan_slug}")

            user = self._get_or_create_user(session, telegram_id)
            now = datetime.now(self.timezone)
            expires_at = now + timedelta(days=plan.duration_days)

            subscription = session.scalar(
                select(Subscription)
                .where(Subscription.user_id == user.id, Subscription.status == "active")
                .order_by(Subscription.expires_at.desc())
            )
            if subscription:
                subscription.plan_id = plan.id
                subscription.device_limit = plan.device_limit
                subscription.starts_at = now
                subscription.expires_at = expires_at
            else:
                subscription = Subscription(
                    user_id=user.id,
                    plan_id=plan.id,
                    status="active",
                    device_limit=plan.device_limit,
                    starts_at=now,
                    expires_at=expires_at,
                )
                session.add(subscription)
                session.flush()

            session.add(
                Payment(
                    user_id=user.id,
                    subscription_id=subscription.id,
                    plan_id=plan.id,
                    provider="mock",
                    amount=plan.price_rub,
                    currency="RUB",
                    status="succeeded",
                )
            )
            session.commit()
            return self._load_subscription_view(session, telegram_id) or SubscriptionView(
                telegram_id=telegram_id,
                plan=self._plan_view(plan),
                expires_at=expires_at,
            )

    def add_device(self, telegram_id: int, preset_slug: str) -> DeviceView:
        preset = get_device_preset(preset_slug)
        connection_uri = ""

        with self._session_factory() as session:
            subscription = self._get_active_subscription(session, telegram_id)
            if not subscription:
                raise NoSubscriptionError("Сначала выберите тариф.")

            device_count = session.scalar(
                select(func.count())
                .select_from(Device)
                .where(
                    Device.subscription_id == subscription.id,
                    Device.status == "active",
                )
            ) or 0
            if device_count >= subscription.device_limit:
                raise DeviceLimitExceededError(
                    "Лимит устройств исчерпан.\nУдалите одно из существующих устройств."
                )

            duplicate = session.scalar(
                select(Device.id)
                .where(
                    Device.subscription_id == subscription.id,
                    Device.device_slug == preset.slug,
                    Device.status == "active",
                )
            )
            if duplicate is not None:
                raise DeviceAlreadyExistsError(f"{preset.title} уже добавлено.")

            xray_uuid = str(uuid4())
            xray_email = f"{telegram_id}_{preset.email_suffix}"
            connection_uri = self._build_connection_uri(xray_uuid, preset.title)

            if self._xray_agent:
                try:
                    self._xray_agent.add_user(email=xray_email, uuid=xray_uuid, limit=1)
                except XrayAgentClientError as exc:
                    raise RuntimeError(f"Не удалось добавить устройство в Xray: {exc}") from exc

            device = Device(
                user_id=subscription.user_id,
                subscription_id=subscription.id,
                uuid=xray_uuid,
                device_id=make_device_id(subscription.user_id, preset.slug, xray_uuid),
                device_name=preset.title,
                device_slug=preset.slug,
                xray_email=xray_email,
                status="active",
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            return DeviceView(
                id=device.id,
                slug=device.device_slug,
                emoji=preset.emoji,
                display_name=device.device_name,
                xray_uuid=device.uuid,
                xray_email=device.xray_email,
                connection_uri=connection_uri,
                created_at=device.created_at,
            )

    def remove_device(self, telegram_id: int, device_id: int) -> None:
        with self._session_factory() as session:
            device = session.scalar(
                select(Device)
                .join(User, Device.user_id == User.id)
                .where(Device.id == device_id, User.telegram_id == telegram_id)
            )
            if not device:
                raise DeviceNotFoundError("Устройство не найдено.")

            if self._xray_agent and device.status == "active":
                try:
                    self._xray_agent.remove_user(uuid=device.uuid)
                except XrayAgentClientError as exc:
                    raise RuntimeError(f"Не удалось удалить устройство в Xray: {exc}") from exc

            session.delete(device)
            session.commit()

    def get_device(self, telegram_id: int, device_id: int) -> DeviceView | None:
        with self._session_factory() as session:
            device = session.scalar(
                select(Device)
                .join(User, Device.user_id == User.id)
                .where(
                    Device.id == device_id,
                    User.telegram_id == telegram_id,
                    Device.status == "active",
                )
            )
            if not device:
                return None
            preset = get_device_preset(device.device_slug)
            return DeviceView(
                id=device.id,
                slug=device.device_slug,
                emoji=preset.emoji,
                display_name=device.device_name,
                xray_uuid=device.uuid,
                xray_email=device.xray_email,
                connection_uri=self._build_connection_uri(device.uuid, device.device_name),
                created_at=device.created_at,
            )

    def _get_or_create_user(self, session: Session, telegram_id: int) -> User:
        user = session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user:
            return user
        user = User(telegram_id=telegram_id, status="active")
        session.add(user)
        session.flush()
        return user

    def _get_active_subscription(self, session: Session, telegram_id: int) -> Subscription | None:
        return session.scalar(
            select(Subscription)
            .join(User, Subscription.user_id == User.id)
            .where(User.telegram_id == telegram_id, Subscription.status == "active")
            .options(joinedload(Subscription.plan))
            .order_by(Subscription.expires_at.desc())
        )

    def _load_subscription_view(self, session: Session, telegram_id: int) -> SubscriptionView | None:
        subscription = self._get_active_subscription(session, telegram_id)
        if not subscription:
            return None

        devices = session.scalars(
            select(Device)
            .join(User, Device.user_id == User.id)
            .where(
                User.telegram_id == telegram_id,
                Device.subscription_id == subscription.id,
                Device.status == "active",
            )
            .order_by(Device.created_at)
        ).all()

        device_views = tuple(
            DeviceView(
                id=device.id,
                slug=device.device_slug,
                emoji=get_device_preset(device.device_slug).emoji,
                display_name=device.device_name,
                xray_uuid=device.uuid,
                xray_email=device.xray_email,
                connection_uri=self._build_connection_uri(device.uuid, device.device_name),
                created_at=device.created_at,
            )
            for device in devices
        )

        return SubscriptionView(
            telegram_id=telegram_id,
            plan=self._plan_view(subscription.plan),
            expires_at=subscription.expires_at or datetime.now(self.timezone),
            devices=device_views,
        )

    def _plan_view(self, plan: Plan) -> PlanView:
        return PlanView(
            slug=plan.slug,
            name=plan.name,
            description=plan.description or "",
            price_rub=int(plan.price_rub),
            device_limit=plan.device_limit,
            duration_days=plan.duration_days,
        )

    def _build_connection_uri(self, uuid: str, label: str) -> str:
        if not self.reality_public_key:
            raise RuntimeError("Задайте REALITY_PUBLIC_KEY в .env")
        return build_vless_reality_uri(
            uuid,
            self.public_host,
            label,
            port=self.public_port,
            public_key=self.reality_public_key,
            short_id=self.reality_short_id,
            sni=self.reality_sni,
            flow=self.vless_flow,
        )
