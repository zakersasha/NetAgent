from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Plan:
    slug: str
    name: str
    description: str
    price_rub: int
    traffic_limit_gb: int | None
    duration_days: int = 30
    product_type: str = "vpn"
    device_limit: int = 1


PLANS: tuple[Plan, ...] = (
    Plan(
        slug="combo_max",
        name="Семья",
        description="до 5 устройств · семья + AI-помощник",
        price_rub=399,
        traffic_limit_gb=150,
        product_type="bundle",
        device_limit=5,
    ),
    Plan(
        slug="combo",
        name="Стандарт",
        description="до 3 устройств · канал и AI-помощник",
        price_rub=279,
        traffic_limit_gb=80,
        product_type="bundle",
        device_limit=3,
    ),
    Plan(
        slug="connect_plus",
        name="Команда",
        description="до 3 устройств · малая команда",
        price_rub=249,
        traffic_limit_gb=80,
        device_limit=3,
    ),
    Plan(
        slug="connect",
        name="Личный",
        description="1 устройство · личная подписка",
        price_rub=149,
        traffic_limit_gb=40,
        device_limit=1,
    ),
    Plan(
        slug="lite_ai",
        name="AI Помощник",
        description="AI-помощник в Telegram без лимита",
        price_rub=99,
        traffic_limit_gb=None,
        product_type="ai",
        device_limit=0,
    ),
)


def get_plan(slug: str) -> Plan:
    for plan in PLANS:
        if plan.slug == slug:
            return plan
    raise ValueError(f"Unknown plan: {slug}")
