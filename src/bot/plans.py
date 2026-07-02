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
        description="до 10 устройств · семья и расширенная команда + AI",
        price_rub=449,
        traffic_limit_gb=200,
        product_type="bundle",
        device_limit=10,
    ),
    Plan(
        slug="combo",
        name="Бизнес",
        description="до 5 устройств · команда + AI-помощник",
        price_rub=299,
        traffic_limit_gb=80,
        product_type="bundle",
        device_limit=5,
    ),
    Plan(
        slug="connect_plus",
        name="Команда",
        description="до 3 устройств · удалённая работа команды",
        price_rub=279,
        traffic_limit_gb=100,
        device_limit=3,
    ),
    Plan(
        slug="connect",
        name="Личный",
        description="1 устройство · личная подписка · защищённый канал",
        price_rub=179,
        traffic_limit_gb=50,
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
