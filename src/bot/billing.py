from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from bot.device_presets import DevicePreset, VPN_KEY_PRESET, get_device_preset
from bot.plans import Plan as PlanView
from bot.xray_provisioner import XrayProvisioner, XrayProvisionerError
from netagent_common.device_id import make_device_id
from netagent_common.vless_uri import build_vless_reality_uri
from netagent_db.models import Device, Payment, Plan, Subscription, User


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


EARLY_RENEWAL_DAYS = 5


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
    __slots__ = (
        "telegram_id",
        "plan",
        "expires_at",
        "devices",
        "days_left",
        "traffic_used_bytes",
        "traffic_limit_gb",
    )

    def __init__(
        self,
        telegram_id: int,
        plan: PlanView,
        expires_at: datetime,
        devices: tuple[DeviceView, ...] = (),
        days_left: int = 0,
        traffic_used_bytes: int = 0,
        traffic_limit_gb: int | None = None,
    ) -> None:
        self.telegram_id = telegram_id
        self.plan = plan
        self.expires_at = expires_at
        self.devices = devices
        self.days_left = days_left
        self.traffic_used_bytes = traffic_used_bytes
        self.traffic_limit_gb = traffic_limit_gb


class AccountStatusView:
    __slots__ = (
        "telegram_id",
        "vpn_subscription",
        "ai_subscription",
        "ai_free_remaining",
        "has_ai_unlimited",
    )

    def __init__(
        self,
        telegram_id: int,
        vpn_subscription: SubscriptionView | None,
        ai_subscription: SubscriptionView | None,
        ai_free_remaining: int,
        has_ai_unlimited: bool,
    ) -> None:
        self.telegram_id = telegram_id
        self.vpn_subscription = vpn_subscription
        self.ai_subscription = ai_subscription
        self.ai_free_remaining = ai_free_remaining
        self.has_ai_unlimited = has_ai_unlimited


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
        xray_provisioner: XrayProvisioner | None = None,
        ai_free_daily_limit: int = 3,
    ) -> None:
        self._session_factory = session_factory
        self.public_host = public_host
        self.public_port = public_port
        self.timezone = ZoneInfo(timezone)
        self.reality_public_key = reality_public_key.strip()
        self.reality_sni = reality_sni
        self.reality_short_id = reality_short_id
        self.vless_flow = vless_flow
        self._xray = xray_provisioner or XrayProvisioner(client=None, required=False)
        self._ai_free_daily_limit = max(1, ai_free_daily_limit)

    def plans(self, product_type: str | None = None) -> tuple[PlanView, ...]:
        with self._session_factory() as session:
            query = select(Plan).where(Plan.is_active.is_(True))
            if product_type:
                if product_type == "bundle":
                    query = query.where(Plan.product_type == "bundle")
                elif product_type == "vpn":
                    query = query.where(Plan.product_type == "vpn")
                elif product_type == "ai":
                    query = query.where(Plan.product_type == "ai")
                elif product_type == "shop":
                    query = query.where(Plan.product_type.in_(("bundle", "vpn", "ai")))
            rows = session.scalars(query.order_by(Plan.sort_order)).all()
            return tuple(self._plan_view(row) for row in rows)

    def get_plan(self, slug: str) -> PlanView | None:
        with self._session_factory() as session:
            row = session.scalar(select(Plan).where(Plan.slug == slug, Plan.is_active.is_(True)))
            return self._plan_view(row) if row else None

    def get_account_status(self, telegram_id: int) -> AccountStatusView:
        with self._session_factory() as session:
            vpn_sub = self._load_subscription_view(session, telegram_id, line="vpn")
            ai_sub = self._load_subscription_view(session, telegram_id, line="ai")
            has_ai = ai_sub is not None
            free_remaining = self._ai_free_daily_limit
            if not has_ai:
                user = session.scalar(select(User).where(User.telegram_id == telegram_id))
                if user:
                    from netagent_db.models import AiDailyUsage

                    today = datetime.now(self.timezone).date()
                    used = session.scalar(
                        select(AiDailyUsage.message_count).where(
                            AiDailyUsage.user_id == user.id,
                            AiDailyUsage.usage_date == today,
                        )
                    ) or 0
                    free_remaining = max(0, self._ai_free_daily_limit - used)
            return AccountStatusView(
                telegram_id=telegram_id,
                vpn_subscription=vpn_sub,
                ai_subscription=ai_sub,
                ai_free_remaining=free_remaining,
                has_ai_unlimited=has_ai,
            )

    def get_subscription(self, telegram_id: int) -> SubscriptionView | None:
        with self._session_factory() as session:
            return self._load_subscription_view(session, telegram_id, line="vpn")

    def get_ai_subscription(self, telegram_id: int) -> SubscriptionView | None:
        with self._session_factory() as session:
            return self._load_subscription_view(session, telegram_id, line="ai")

    def can_purchase_plan(self, telegram_id: int, plan_slug: str) -> tuple[bool, str | None]:
        with self._session_factory() as session:
            plan = session.scalar(select(Plan).where(Plan.slug == plan_slug, Plan.is_active.is_(True)))
            if not plan:
                return False, f"Unknown plan: {plan_slug}"
            user = session.scalar(select(User).where(User.telegram_id == telegram_id))
            if not user:
                return True, None
            return self._can_purchase_plan(session, user.id, plan)

    def can_purchase_plan_for_user(self, user_id: int, plan_slug: str) -> tuple[bool, str | None]:
        with self._session_factory() as session:
            plan = session.scalar(select(Plan).where(Plan.slug == plan_slug, Plan.is_active.is_(True)))
            if not plan:
                return False, f"Unknown plan: {plan_slug}"
            user = session.get(User, user_id)
            if not user:
                return False, "User not found"
            return self._can_purchase_plan(session, user.id, plan)

    def activate_mock_payment(self, telegram_id: int, plan_slug: str) -> SubscriptionView:
        with self._session_factory() as session:
            plan = session.scalar(select(Plan).where(Plan.slug == plan_slug, Plan.is_active.is_(True)))
            if not plan:
                raise BillingError(f"Unknown plan: {plan_slug}")

            user = self._get_or_create_user(session, telegram_id)
            allowed, reason = self._can_purchase_plan(session, user.id, plan)
            if not allowed:
                raise BillingError(reason or "Оплата сейчас недоступна")
            now = datetime.now(self.timezone)
            expires_at = now + timedelta(days=plan.duration_days)

            types_to_expire = self._conflicting_product_types(plan.product_type)

            old_sub_ids = list(
                session.scalars(
                    select(Subscription.id)
                    .join(Plan, Subscription.plan_id == Plan.id)
                    .where(
                        Subscription.user_id == user.id,
                        Subscription.status == "active",
                        Plan.product_type.in_(types_to_expire),
                    )
                ).all()
            )

            self._expire_conflicting_subscriptions(session, user.id, plan.product_type)

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

            if plan.product_type in ("vpn", "bundle") and old_sub_ids:
                for device in session.scalars(
                    select(Device).where(Device.subscription_id.in_(old_sub_ids))
                ).all():
                    device.subscription_id = subscription.id

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

            if plan.product_type in ("vpn", "bundle"):
                try:
                    self.ensure_vpn_key(telegram_id)
                except (XrayProvisionerError, RuntimeError):
                    pass

            line = "vpn" if plan.product_type in ("vpn", "bundle") else "ai"
            return self._load_subscription_view(session, telegram_id, line=line) or SubscriptionView(
                telegram_id=telegram_id,
                plan=self._plan_view(plan),
                expires_at=expires_at,
                days_left=self._days_left(expires_at),
                traffic_limit_gb=plan.traffic_limit_gb,
            )

    def ensure_vpn_key(self, telegram_id: int) -> DeviceView:
        """One VPN key per subscription. Returns existing key if already created."""
        preset = VPN_KEY_PRESET
        with self._session_factory() as session:
            subscription = self._get_active_subscription(session, telegram_id, line="vpn")
            if not subscription:
                raise NoSubscriptionError("Сначала выберите тариф.")

            existing = session.scalar(
                select(Device)
                .join(User, Device.user_id == User.id)
                .where(
                    User.telegram_id == telegram_id,
                    Device.subscription_id == subscription.id,
                    Device.status == "active",
                )
            )
            if existing:
                return self._device_view(existing, preset)

            return self._create_vpn_device(session, subscription, preset)

    def regenerate_vpn_key(self, telegram_id: int) -> DeviceView:
        """Revoke old key and issue a new one (e.g. if shared)."""
        preset = VPN_KEY_PRESET
        with self._session_factory() as session:
            subscription = self._get_active_subscription(session, telegram_id, line="vpn")
            if not subscription:
                raise NoSubscriptionError("Сначала выберите тариф.")

            existing = session.scalar(
                select(Device)
                .join(User, Device.user_id == User.id)
                .where(
                    User.telegram_id == telegram_id,
                    Device.subscription_id == subscription.id,
                    Device.status == "active",
                )
            )
            if existing:
                try:
                    self._xray.revoke_key(uuid=existing.uuid)
                except XrayProvisionerError as exc:
                    raise RuntimeError(str(exc)) from exc
                session.delete(existing)
                session.flush()

            return self._create_vpn_device(session, subscription, preset)

    def add_device(self, telegram_id: int, preset_slug: str = VPN_KEY_PRESET.slug) -> DeviceView:
        return self.ensure_vpn_key(telegram_id)

    def _create_vpn_device(
        self,
        session: Session,
        subscription: Subscription,
        preset: DevicePreset,
    ) -> DeviceView:
        user = session.get(User, subscription.user_id)
        if not user:
            raise BillingError("User not found")
        xray_uuid = str(uuid4())
        xray_email = self._vpn_email(user, preset.email_suffix)
        connection_uri = self._build_connection_uri(xray_uuid, preset.title)

        self._xray.provision_key(email=xray_email, uuid=xray_uuid)

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
        try:
            session.commit()
        except Exception:
            session.rollback()
            self._xray.rollback_key(uuid=xray_uuid)
            raise
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

    def _device_view(self, device: Device, preset) -> DeviceView:
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

    def remove_device(self, telegram_id: int, device_id: int) -> None:
        with self._session_factory() as session:
            device = session.scalar(
                select(Device)
                .join(User, Device.user_id == User.id)
                .where(Device.id == device_id, User.telegram_id == telegram_id)
            )
            if not device:
                raise DeviceNotFoundError("Устройство не найдено.")

            if device.status == "active":
                try:
                    self._xray.revoke_key(uuid=device.uuid)
                except XrayProvisionerError as exc:
                    raise RuntimeError(str(exc)) from exc

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

    def _get_active_subscription(
        self,
        session: Session,
        telegram_id: int,
        line: str = "vpn",
    ) -> Subscription | None:
        now = datetime.now(self.timezone)
        product_types = self._product_types_for_line(line)
        return session.scalar(
            select(Subscription)
            .join(User, Subscription.user_id == User.id)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(
                User.telegram_id == telegram_id,
                Subscription.status == "active",
                Plan.product_type.in_(product_types),
                Subscription.expires_at.is_not(None),
                Subscription.expires_at > now,
            )
            .options(joinedload(Subscription.plan))
            .order_by(Subscription.expires_at.desc())
        )

    def _load_subscription_view(
        self,
        session: Session,
        telegram_id: int,
        line: str = "vpn",
    ) -> SubscriptionView | None:
        subscription = self._get_active_subscription(session, telegram_id, line)
        if not subscription:
            return None

        devices: tuple[DeviceView, ...] = ()
        if line == "vpn" and subscription.plan.product_type in ("vpn", "bundle"):
            devices = self._load_device_views(session, telegram_id, subscription)

        expires_at = subscription.expires_at or datetime.now(self.timezone)
        return SubscriptionView(
            telegram_id=telegram_id,
            plan=self._plan_view(subscription.plan),
            expires_at=expires_at,
            devices=devices,
            days_left=self._days_left(expires_at),
            traffic_used_bytes=int(subscription.traffic_used_bytes or 0),
            traffic_limit_gb=subscription.plan.traffic_limit_gb,
        )

    def _load_device_views(
        self,
        session: Session,
        telegram_id: int,
        subscription: Subscription,
    ) -> tuple[DeviceView, ...]:
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
        return tuple(
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

    def _conflicting_product_types(self, purchased_type: str) -> tuple[str, ...]:
        if purchased_type == "bundle":
            return ("vpn", "ai", "bundle")
        if purchased_type == "vpn":
            return ("vpn", "bundle")
        return ("ai", "bundle")

    def _can_purchase_plan(self, session: Session, user_id: int, plan: Plan) -> tuple[bool, str | None]:
        types_to_check = self._conflicting_product_types(plan.product_type)
        subs = session.scalars(
            select(Subscription)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Plan.product_type.in_(types_to_check),
                Subscription.expires_at.is_not(None),
                Subscription.expires_at > datetime.now(self.timezone),
            )
        ).all()
        if not subs:
            return True, None

        max_days_left = max(self._days_left(sub.expires_at) for sub in subs if sub.expires_at)
        if max_days_left > EARLY_RENEWAL_DAYS:
            return False, (
                f"Оплатить можно не раньше чем за {EARLY_RENEWAL_DAYS} дней до окончания подписки. "
                f"Осталось {max_days_left} дн."
            )
        return True, None

    def _expire_conflicting_subscriptions(
        self,
        session: Session,
        user_id: int,
        purchased_type: str,
    ) -> None:
        types_to_expire = self._conflicting_product_types(purchased_type)

        subs = session.scalars(
            select(Subscription)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Plan.product_type.in_(types_to_expire),
            )
        ).all()
        for sub in subs:
            sub.status = "expired"

    def _product_types_for_line(self, line: str) -> tuple[str, ...]:
        if line == "vpn":
            return ("vpn", "bundle")
        return ("ai", "bundle")

    def days_left(self, expires_at: datetime) -> int:
        return self._days_left(expires_at)

    def _days_left(self, expires_at: datetime) -> int:
        now = datetime.now(self.timezone)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=self.timezone)
        delta = expires_at - now
        return max(0, delta.days)

    def _plan_view(self, plan: Plan) -> PlanView:
        return PlanView(
            slug=plan.slug,
            name=plan.name,
            description=plan.description or "",
            price_rub=int(plan.price_rub),
            device_limit=1,
            duration_days=plan.duration_days,
            product_type=plan.product_type,
            traffic_limit_gb=plan.traffic_limit_gb,
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

    # --- Web (user_id / email) ---

    def get_account_status_for_user(self, user_id: int) -> AccountStatusView:
        with self._session_factory() as session:
            user = session.get(User, user_id)
            if not user:
                raise BillingError("User not found")
            vpn_sub = self._load_subscription_view_for_user(session, user_id, line="vpn")
            ai_sub = self._load_subscription_view_for_user(session, user_id, line="ai")
            has_ai = ai_sub is not None
            free_remaining = self._ai_free_daily_limit
            if not has_ai:
                from netagent_db.models import AiDailyUsage

                today = datetime.now(self.timezone).date()
                used = session.scalar(
                    select(AiDailyUsage.message_count).where(
                        AiDailyUsage.user_id == user_id,
                        AiDailyUsage.usage_date == today,
                    )
                ) or 0
                free_remaining = max(0, self._ai_free_daily_limit - used)
            return AccountStatusView(
                telegram_id=user.telegram_id or 0,
                vpn_subscription=vpn_sub,
                ai_subscription=ai_sub,
                ai_free_remaining=free_remaining,
                has_ai_unlimited=has_ai,
            )

    def activate_mock_payment_for_user(self, user_id: int, plan_slug: str) -> SubscriptionView:
        with self._session_factory() as session:
            plan = session.scalar(select(Plan).where(Plan.slug == plan_slug, Plan.is_active.is_(True)))
            if not plan:
                raise BillingError(f"Unknown plan: {plan_slug}")
            user = session.get(User, user_id)
            if not user:
                raise BillingError("User not found")

            allowed, reason = self._can_purchase_plan(session, user.id, plan)
            if not allowed:
                raise BillingError(reason or "Оплата сейчас недоступна")

            now = datetime.now(self.timezone)
            expires_at = now + timedelta(days=plan.duration_days)
            types_to_expire = self._conflicting_product_types(plan.product_type)

            old_sub_ids = list(
                session.scalars(
                    select(Subscription.id)
                    .join(Plan, Subscription.plan_id == Plan.id)
                    .where(
                        Subscription.user_id == user.id,
                        Subscription.status == "active",
                        Plan.product_type.in_(types_to_expire),
                    )
                ).all()
            )
            self._expire_conflicting_subscriptions(session, user.id, plan.product_type)

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

            if plan.product_type in ("vpn", "bundle") and old_sub_ids:
                for device in session.scalars(
                    select(Device).where(Device.subscription_id.in_(old_sub_ids))
                ).all():
                    device.subscription_id = subscription.id

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

            if plan.product_type in ("vpn", "bundle"):
                try:
                    self.ensure_vpn_key_for_user(user_id)
                except (XrayProvisionerError, RuntimeError):
                    pass

            line = "vpn" if plan.product_type in ("vpn", "bundle") else "ai"
            return self._load_subscription_view_for_user(session, user_id, line=line) or SubscriptionView(
                telegram_id=user.telegram_id,
                plan=self._plan_view(plan),
                expires_at=expires_at,
                days_left=self._days_left(expires_at),
                traffic_limit_gb=plan.traffic_limit_gb,
            )

    def ensure_vpn_key_for_user(self, user_id: int) -> DeviceView:
        preset = VPN_KEY_PRESET
        with self._session_factory() as session:
            subscription = self._get_active_subscription_for_user(session, user_id, line="vpn")
            if not subscription:
                raise NoSubscriptionError("Сначала выберите тариф.")
            existing = session.scalar(
                select(Device).where(
                    Device.user_id == user_id,
                    Device.subscription_id == subscription.id,
                    Device.status == "active",
                )
            )
            if existing:
                return self._device_view(existing, preset)
            return self._create_vpn_device(session, subscription, preset)

    def regenerate_vpn_key_for_user(self, user_id: int) -> DeviceView:
        preset = VPN_KEY_PRESET
        with self._session_factory() as session:
            subscription = self._get_active_subscription_for_user(session, user_id, line="vpn")
            if not subscription:
                raise NoSubscriptionError("Сначала выберите тариф.")
            existing = session.scalar(
                select(Device).where(
                    Device.user_id == user_id,
                    Device.subscription_id == subscription.id,
                    Device.status == "active",
                )
            )
            if existing:
                try:
                    self._xray.revoke_key(uuid=existing.uuid)
                except XrayProvisionerError as exc:
                    raise RuntimeError(str(exc)) from exc
                session.delete(existing)
                session.flush()
            return self._create_vpn_device(session, subscription, preset)

    def _vpn_email(self, user: User, suffix: str) -> str:
        if user.telegram_id:
            return f"{user.telegram_id}_{suffix}"
        return f"u{user.id}_{suffix}"

    def _get_active_subscription_for_user(
        self,
        session: Session,
        user_id: int,
        line: str = "vpn",
    ) -> Subscription | None:
        now = datetime.now(self.timezone)
        product_types = self._product_types_for_line(line)
        return session.scalar(
            select(Subscription)
            .join(Plan, Subscription.plan_id == Plan.id)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Plan.product_type.in_(product_types),
                Subscription.expires_at.is_not(None),
                Subscription.expires_at > now,
            )
            .options(joinedload(Subscription.plan))
            .order_by(Subscription.expires_at.desc())
        )

    def _load_subscription_view_for_user(
        self,
        session: Session,
        user_id: int,
        line: str = "vpn",
    ) -> SubscriptionView | None:
        subscription = self._get_active_subscription_for_user(session, user_id, line)
        if not subscription:
            return None
        user = session.get(User, user_id)
        devices: tuple[DeviceView, ...] = ()
        if line == "vpn" and subscription.plan.product_type in ("vpn", "bundle"):
            devices = self._load_device_views_for_user(session, user_id, subscription)
        expires_at = subscription.expires_at or datetime.now(self.timezone)
        return SubscriptionView(
            telegram_id=user.telegram_id if user else None,
            plan=self._plan_view(subscription.plan),
            expires_at=expires_at,
            devices=devices,
            days_left=self._days_left(expires_at),
            traffic_used_bytes=int(subscription.traffic_used_bytes or 0),
            traffic_limit_gb=subscription.plan.traffic_limit_gb,
        )

    def _load_device_views_for_user(
        self,
        session: Session,
        user_id: int,
        subscription: Subscription,
    ) -> tuple[DeviceView, ...]:
        devices = session.scalars(
            select(Device)
            .where(
                Device.user_id == user_id,
                Device.subscription_id == subscription.id,
                Device.status == "active",
            )
            .order_by(Device.created_at)
        ).all()
        return tuple(
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
