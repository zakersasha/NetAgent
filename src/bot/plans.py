from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Plan:
    slug: str
    name: str
    description: str
    price_rub: int
    device_limit: int
    duration_days: int = 30


PLANS: tuple[Plan, ...] = (
    Plan(
        slug="start",
        name="Start",
        description="Для одного телефона или ноутбука",
        price_rub=150,
        device_limit=1,
    ),
    Plan(
        slug="standard",
        name="Standard",
        description="Оптимально: телефон + ноутбук",
        price_rub=250,
        device_limit=2,
    ),
    Plan(
        slug="family",
        name="Family",
        description="Для семьи или нескольких личных устройств",
        price_rub=350,
        device_limit=3,
    ),
)


def get_plan(slug: str) -> Plan:
    for plan in PLANS:
        if plan.slug == slug:
            return plan
    raise ValueError(f"Unknown plan: {slug}")
