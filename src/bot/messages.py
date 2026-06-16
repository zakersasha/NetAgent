from html import escape

from bot.billing import SubscriptionView
from bot.plans import Plan


def welcome_text(service_name: str) -> str:
    return (
        f"🛡 <b>{escape(service_name)}</b>\n\n"
        "Быстрый VPN для Telegram, YouTube, сайтов и приложений.\n"
        "Подключение за пару минут: выберите тариф, оплатите, получите ключ.\n\n"
        "✅ VLESS Reality\n"
        "✅ 30 дней доступа\n"
        "✅ Помощь с подключением\n\n"
        "Выберите действие ниже 👇"
    )


def plans_text(plans: tuple[Plan, ...]) -> str:
    rows = [
        "💎 <b>Тарифы на 30 дней</b>\n",
        "Выберите вариант под ваши устройства:",
    ]
    for plan in plans:
        rows.append(
            f"\n<b>{escape(plan.name)}</b> · {plan.price_rub} ₽\n"
            f"{escape(plan.description)}\n"
            f"До {plan.device_limit} устр."
        )
    return "\n".join(rows)


def plan_details_text(plan: Plan) -> str:
    return (
        f"🚀 <b>{escape(plan.name)}</b>\n\n"
        f"{escape(plan.description)}\n\n"
        f"Срок: <b>{plan.duration_days} дней</b>\n"
        f"Устройств: <b>до {plan.device_limit}</b>\n"
        f"Цена: <b>{plan.price_rub} ₽</b>\n\n"
        "После оплаты бот сразу выдаст ключ для приложения-клиента."
    )


def subscription_text(subscription: SubscriptionView) -> str:
    expires_at = subscription.expires_at.strftime("%d.%m.%Y %H:%M MSK")
    return (
        "✅ <b>Подписка активна</b>\n\n"
        f"Тариф: <b>{escape(subscription.plan.name)}</b>\n"
        f"Устройств: <b>до {subscription.plan.device_limit}</b>\n"
        f"Действует до: <b>{expires_at}</b>\n\n"
        "🔑 <b>Ваш ключ</b>\n"
        f"<code>{escape(subscription.connection_uri)}</code>\n\n"
        "Скопируйте ключ и импортируйте его в приложение для VLESS/Xray."
    )


def no_subscription_text() -> str:
    return (
        "🔑 <b>Активной подписки пока нет</b>\n\n"
        "Выберите тариф, и бот сразу выдаст ключ для подключения."
    )


def activating_text() -> str:
    return (
        "⏳ <b>Оплата прошла</b>\n\n"
        "Создаю ваш VPN-ключ. Обычно это занимает несколько секунд."
    )


def activation_error_text(error: str) -> str:
    return (
        "⚠️ <b>Не удалось активировать ключ</b>\n\n"
        f"{escape(error)}\n\n"
        "Попробуйте ещё раз или напишите в поддержку."
    )


def help_text(support_contact: str) -> str:
    return (
        "❓ <b>Помощь</b>\n\n"
        "1. Купите тариф.\n"
        "2. Скопируйте ключ.\n"
        "3. Импортируйте его в приложение с поддержкой VLESS Reality.\n\n"
        f"Поддержка: {escape(support_contact)}"
    )
