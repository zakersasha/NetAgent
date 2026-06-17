from html import escape

from bot.billing import SubscriptionView
from bot.plans import Plan


def welcome_text(service_name: str) -> str:
    return (
        f"👋 <b>Добро пожаловать в {escape(service_name)}</b>\n\n"
        "Стабильный личный канал для работы, учёбы и развлечений — "
        "без сложных настроек.\n\n"
        "✨ Быстрое подключение\n"
        "📱 Телефон, ПК и планшет\n"
        "🔑 Ключ в боте за пару минут\n"
        "🛟 Помощь, если что-то непонятно\n\n"
        "Выберите действие ниже 👇"
    )


def plans_text(plans: tuple[Plan, ...]) -> str:
    rows = [
        "📦 <b>Тарифы на 30 дней</b>\n",
        "Выберите вариант по числу устройств:",
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
        f"✨ <b>{escape(plan.name)}</b>\n\n"
        f"{escape(plan.description)}\n\n"
        f"Срок: <b>{plan.duration_days} дней</b>\n"
        f"Устройств: <b>до {plan.device_limit}</b>\n"
        f"Цена: <b>{plan.price_rub} ₽</b>\n\n"
        "После оплаты бот выдаст ключ — скопируйте его в приложение из раздела «Инструкции»."
    )


def subscription_text(subscription: SubscriptionView) -> str:
    expires_at = subscription.expires_at.strftime("%d.%m.%Y %H:%M MSK")
    return (
        "✅ <b>Доступ активен</b>\n\n"
        f"Тариф: <b>{escape(subscription.plan.name)}</b>\n"
        f"Устройств: <b>до {subscription.plan.device_limit}</b>\n"
        f"Действует до: <b>{expires_at}</b>\n\n"
        "🔑 <b>Ваш ключ</b>\n"
        f"<code>{escape(subscription.connection_uri)}</code>\n\n"
        "Скопируйте ключ целиком и добавьте в приложение — шаги в «Инструкции»."
    )


def no_subscription_text() -> str:
    return (
        "🔑 <b>Ключа пока нет</b>\n\n"
        "Выберите тариф — бот выдаст персональный ключ для подключения."
    )


def activating_text() -> str:
    return (
        "⏳ <b>Оплата прошла</b>\n\n"
        "Готовлю ваш ключ. Обычно это занимает несколько секунд."
    )


def activation_error_text(error: str) -> str:
    return (
        "⚠️ <b>Не удалось выдать ключ</b>\n\n"
        f"{escape(error)}\n\n"
        "Попробуйте ещё раз или напишите в поддержку."
    )


def instructions_text() -> str:
    return (
        "📖 <b>Как подключиться</b>\n\n"
        "1. Получите ключ в «Мой ключ» или после оплаты тарифа.\n"
        "2. Установите приложение на устройство.\n"
        "3. Добавьте ключ через «Импорт из буфера» или «+» → вставить ссылку.\n"
        "4. Включите подключение в приложении.\n\n"
        "<b>Рекомендуемые приложения</b>\n\n"
        "📱 <b>Android</b>\n"
        "• <a href=\"https://play.google.com/store/apps/details?id=com.v2ray.ang\">v2rayNG</a> (Google Play)\n"
        "• <a href=\"https://play.google.com/store/apps/details?id=app.hiddify.com\">Hiddify</a> (Google Play)\n\n"
        "🍎 <b>iPhone / iPad</b>\n"
        "• <a href=\"https://apps.apple.com/app/streisand/id6450534064\">Streisand</a> (App Store)\n"
        "• <a href=\"https://apps.apple.com/app/v2raytun/id6476628951\">v2RayTun</a> (App Store)\n"
        "• <a href=\"https://apps.apple.com/app/hiddify-proxy-vpn/id6594877714\">Hiddify</a> (App Store)\n\n"
        "💻 <b>Windows / macOS</b>\n"
        "• <a href=\"https://github.com/hiddify/hiddify-app/releases\">Hiddify Desktop</a>\n"
        "• <a href=\"https://github.com/2dust/v2rayN/releases\">v2rayN</a> (Windows)\n"
        "• <a href=\"https://github.com/MatsuriDayo/nekoray/releases\">Nekoray</a> (Windows / macOS)\n\n"
        "Если не подключается — откройте «Поддержка», мы поможем."
    )
