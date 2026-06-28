from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Plan:
    slug: str
    name: str
    description: str
    price_rub: int
    device_limit: int
    duration_days: int = 30
    product_type: str = "vpn"


PLANS: tuple[Plan, ...] = (
    Plan(
        slug="combo_max",
        name="Combo Max",
        description="3 устройства + AI без лимита — для семьи",
        price_rub=449,
        device_limit=3,
        product_type="bundle",
    ),
    Plan(
        slug="combo",
        name="Combo",
        description="Подключение + AI без лимита · 1 устройство",
        price_rub=299,
        device_limit=1,
        product_type="bundle",
    ),
    Plan(
        slug="connect_plus",
        name="Connect+",
        description="Стабильное подключение · 2 устройства",
        price_rub=279,
        device_limit=2,
    ),
    Plan(
        slug="connect",
        name="Connect",
        description="Стабильное подключение · 1 устройство",
        price_rub=179,
        device_limit=1,
    ),
    Plan(
        slug="lite_ai",
        name="Lite AI",
        description="AI-ассистент без лимита сообщений",
        price_rub=99,
        device_limit=0,
        product_type="ai",
    ),
)


def get_plan(slug: str) -> Plan:
    for plan in PLANS:
        if plan.slug == slug:
            return plan
    raise ValueError(f"Unknown plan: {slug}")
