from bot.billing import SubscriptionView
from bot.plans import Plan


def welcome_text(service_name: str) -> str:
    return (
        f"{service_name}\n\n"
        "MVP-бот для продажи VPN-подписок.\n"
        "Сейчас оплата работает в тестовом режиме."
    )


def plans_text(plans: tuple[Plan, ...]) -> str:
    rows = ["Выберите месячный тариф:"]
    for plan in plans:
        rows.append(
            f"\n{plan.name} — {plan.price_rub} ₽\n"
            f"{plan.description}\n"
            f"Лимит устройств: {plan.device_limit}"
        )
    return "\n".join(rows)


def plan_details_text(plan: Plan) -> str:
    return (
        f"Тариф {plan.name}\n\n"
        f"{plan.description}\n"
        f"Срок: {plan.duration_days} дней\n"
        f"Устройств: {plan.device_limit}\n"
        f"Цена: {plan.price_rub} ₽\n\n"
        "Оплата пока тестовая: после нажатия подписка активируется сразу."
    )


def subscription_text(subscription: SubscriptionView) -> str:
    expires_at = subscription.expires_at.strftime("%d.%m.%Y %H:%M MSK")
    return (
        "Подписка активна.\n\n"
        f"Тариф: {subscription.plan.name}\n"
        f"Устройств: {subscription.plan.device_limit}\n"
        f"Действует до: {expires_at}\n\n"
        "Ключ подключения:\n"
        f"`{subscription.connection_uri}`"
    )


def no_subscription_text() -> str:
    return "У вас пока нет активной подписки. Выберите тариф и оплатите тестовый платёж."
