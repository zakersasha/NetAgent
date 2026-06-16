from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid5, NAMESPACE_URL
from zoneinfo import ZoneInfo

from netagent_common.vless_uri import build_vless_reality_uri
from xray_client.client import XrayAgentClient, XrayAgentClientError

from bot.plans import PLANS, Plan, get_plan


@dataclass(frozen=True, slots=True)
class SubscriptionView:
    telegram_id: int
    plan: Plan
    xray_uuid: str
    xray_email: str
    connection_uri: str
    expires_at: datetime


class MockBillingClient:
    """Temporary in-memory billing adapter used until the API service is implemented."""

    def __init__(
        self,
        public_host: str,
        timezone: str = "Europe/Moscow",
        reality_public_key: str = "",
        reality_sni: str = "www.wikipedia.org",
        reality_short_id: str = "6ba85179e30d4fc3",
        vless_flow: str = "xtls-rprx-vision",
        xray_agent: XrayAgentClient | None = None,
    ) -> None:
        self.public_host = public_host
        self.timezone = ZoneInfo(timezone)
        self.reality_public_key = reality_public_key.strip()
        self.reality_sni = reality_sni
        self.reality_short_id = reality_short_id
        self.vless_flow = vless_flow
        self._xray_agent = xray_agent
        self._subscriptions: dict[int, SubscriptionView] = {}

    def plans(self) -> tuple[Plan, ...]:
        return PLANS

    def get_subscription(self, telegram_id: int) -> SubscriptionView | None:
        return self._subscriptions.get(telegram_id)

    def activate_mock_payment(self, telegram_id: int, plan_slug: str) -> SubscriptionView:
        plan = get_plan(plan_slug)
        xray_uuid = self._stable_uuid(telegram_id)
        xray_email = f"user_tg_{telegram_id}@netagent.local"
        expires_at = datetime.now(self.timezone) + timedelta(days=plan.duration_days)
        label = f"NetAgent-{plan.name}"
        connection_uri = self._provision_xray_user(
            uuid=xray_uuid,
            email=xray_email,
            limit=plan.device_limit,
            label=label,
        )

        subscription = SubscriptionView(
            telegram_id=telegram_id,
            plan=plan,
            xray_uuid=xray_uuid,
            xray_email=xray_email,
            connection_uri=connection_uri,
            expires_at=expires_at,
        )
        self._subscriptions[telegram_id] = subscription
        return subscription

    def _stable_uuid(self, telegram_id: int) -> str:
        return str(uuid5(NAMESPACE_URL, f"netagent:telegram:{telegram_id}"))

    def _provision_xray_user(self, uuid: str, email: str, limit: int, label: str) -> str:
        if self._xray_agent:
            try:
                self._xray_agent.add_user(email=email, uuid=uuid, limit=limit)
            except XrayAgentClientError as exc:
                raise RuntimeError(f"Не удалось добавить пользователя в Xray: {exc}") from exc

        if not self.reality_public_key:
            raise RuntimeError("Задайте REALITY_PUBLIC_KEY в .env")

        return build_vless_reality_uri(
            uuid,
            self.public_host,
            label,
            public_key=self.reality_public_key,
            short_id=self.reality_short_id,
            sni=self.reality_sni,
            flow=self.vless_flow,
        )
