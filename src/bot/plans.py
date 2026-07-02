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
    device_limit: int = 1  # legacy DB column, not used in UI


PLANS: tuple[Plan, ...] = (
    Plan(
        slug="combo_max",
        name="Combo Max",
        description="200 ГБ + AI без лимита — для семьи и активного использования",
        price_rub=449,
        traffic_limit_gb=200,
        product_type="bundle",
    ),
    Plan(
        slug="combo",
        name="Combo",
        description="80 ГБ + AI без лимита — лучший выбор",
        price_rub=299,
        traffic_limit_gb=80,
        product_type="bundle",
    ),
    Plan(
        slug="connect_plus",
        name="Connect+",
        description="Стабильное подключение · 100 ГБ в месяц",
        price_rub=279,
        traffic_limit_gb=100,
    ),
    Plan(
        slug="connect",
        name="Connect",
        description="Стабильное подключение · 50 ГБ в месяц",
        price_rub=179,
        traffic_limit_gb=50,
    ),
    Plan(
        slug="lite_ai",
        name="Lite AI",
        description="AI-помощник без лимита сообщений в Telegram",
        price_rub=99,
        traffic_limit_gb=None,
        product_type="ai",
    ),
)


def get_plan(slug: str) -> Plan:
    for plan in PLANS:
        if plan.slug == slug:
            return plan
    raise ValueError(f"Unknown plan: {slug}")
