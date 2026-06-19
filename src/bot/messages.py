from html import escape

from bot.billing import DeviceView, SubscriptionView
from bot.device_presets import DEVICE_PRESETS, DevicePreset
from bot.plans import Plan


def welcome_text(service_name: str) -> str:
    return (
        f"👋 <b>Добро пожаловать в {escape(service_name)}</b>\n\n"
        "Стабильный личный канал для работы, учёбы и развлечений — "
        "без сложных настроек.\n\n"
        "✨ Быстрое подключение\n"
        "📱 Телефон, ПК и планшет\n"
        "🔑 Отдельный ключ на каждое устройство\n"
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
        "После оплаты добавьте устройства в «Мой ключ» — "
        "на каждое будет отдельный ключ."
    )


def payment_success_text(subscription: SubscriptionView) -> str:
    expires_at = subscription.expires_at.strftime("%d.%m.%Y %H:%M MSK")
    return (
        "✅ <b>Тариф активирован</b>\n\n"
        f"Тариф: <b>{escape(subscription.plan.name)}</b>\n"
        f"Максимум устройств: <b>{subscription.plan.device_limit}</b>\n"
        f"Действует до: <b>{expires_at}</b>\n\n"
        "Теперь добавьте устройства и получите ключи для каждого."
    )


def devices_text(subscription: SubscriptionView) -> str:
    expires_at = subscription.expires_at.strftime("%d.%m.%Y %H:%M MSK")
    rows = [
        "🔑 <b>Мои устройства</b>\n",
        f"Тариф: <b>{escape(subscription.plan.name)}</b>",
        f"Максимум устройств: <b>{subscription.plan.device_limit}</b>",
        f"Действует до: <b>{expires_at}</b>",
    ]
    if not subscription.devices:
        rows.append("\n\nУстройств ещё нет. Добавьте первое 👇")
    else:
        rows.append("\n\n<b>Подключённые устройства:</b>")
        for device in subscription.devices:
            rows.append(f"\n{device.emoji} {escape(device.display_name)}")
        rows.append("\n\nНажмите на устройство, чтобы получить ключ.")
    return "\n".join(rows)


def device_detail_text(device: DeviceView) -> str:
    return (
        f"{device.emoji} <b>{escape(device.display_name)}</b>\n\n"
        "🔑 <b>Ключ для этого устройства</b>\n"
        f"<code>{escape(device.connection_uri)}</code>\n\n"
        "Скопируйте ключ и добавьте только на это устройство. "
        "Шаги подключения — в «Инструкции»."
    )


def add_device_text(subscription: SubscriptionView) -> str:
    return (
        "➕ <b>Добавить устройство</b>\n\n"
        f"Можно добавить ещё: <b>"
        f"{subscription.plan.device_limit - len(subscription.devices)}</b>\n\n"
        "Выберите тип устройства — для каждого будет отдельный ключ."
    )


def no_subscription_text() -> str:
    return (
        "🔑 <b>Активного тарифа нет</b>\n\n"
        "Выберите тариф, затем добавьте устройства и получите ключи."
    )


def activating_text() -> str:
    return (
        "⏳ <b>Оплата прошла</b>\n\n"
        "Активируем тариф. Обычно это занимает пару секунд."
    )


def adding_device_text() -> str:
    return (
        "⏳ <b>Добавляем устройство</b>\n\n"
        "Создаём персональный ключ. Обычно это занимает несколько секунд."
    )


def activation_error_text(error: str) -> str:
    return (
        "⚠️ <b>Не удалось выполнить действие</b>\n\n"
        f"{escape(error)}\n\n"
        "Попробуйте ещё раз или напишите в поддержку."
    )


def device_limit_exceeded_text() -> str:
    return (
        "⚠️ <b>Лимит устройств исчерпан</b>\n\n"
        "Удалите одно из существующих устройств, чтобы добавить новое."
    )


def instructions_text() -> str:
    return (
        "📖 <b>Как подключиться</b>\n\n"
        "1. Получите ключ в «Мой ключ» для каждого устройства.\n"
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


def support_text(contact: str) -> str:
    return (
        "💬 <b>Поддержка</b>\n\n"
        f"Напишите нам: <b>{escape(contact)}</b>\n\n"
        "Поможем с оплатой, подключением и настройкой приложения."
    )


def available_presets(subscription: SubscriptionView) -> tuple[DevicePreset, ...]:
    used = {device.slug for device in subscription.devices}
    return tuple(preset for preset in DEVICE_PRESETS if preset.slug not in used)
