from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid5, NAMESPACE_URL
from zoneinfo import ZoneInfo

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

    def __init__(self, public_host: str, timezone: str = "Europe/Moscow") -> None:
        self.public_host = public_host
        self.timezone = ZoneInfo(timezone)
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

        subscription = SubscriptionView(
            telegram_id=telegram_id,
            plan=plan,
            xray_uuid=xray_uuid,
            xray_email=xray_email,
            connection_uri=self._mock_connection_uri(xray_uuid, plan),
            expires_at=expires_at,
        )
        self._subscriptions[telegram_id] = subscription
        return subscription

    def _stable_uuid(self, telegram_id: int) -> str:
        return str(uuid5(NAMESPACE_URL, f"netagent:telegram:{telegram_id}"))

    def _mock_connection_uri(self, xray_uuid: str, plan: Plan) -> str:
        label = f"NetAgent-{plan.name}"
        return (
            f"vless://{xray_uuid}@{self.public_host}:443"
            "?encryption=none&flow=xtls-rprx-vision&security=reality"
            "&sni=www.wikipedia.org&fp=chrome&sid=6ba85179e30d4fc2&type=tcp"
            f"#{label}"
        )
