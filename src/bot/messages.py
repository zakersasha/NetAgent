from html import escape

from bot.billing import AccountStatusView, DeviceView, SubscriptionView
from bot.device_presets import DEVICE_PRESETS, DevicePreset
from bot.plans import Plan


def welcome_text(service_name: str) -> str:
    return (
        f"👋 <b>{escape(service_name)}</b>\n\n"
        "Здесь можно <b>общаться с AI</b> и при необходимости "
        "настроить <b>стабильное подключение</b>.\n\n"
        "🆓 AI — 3 сообщения в день бесплатно\n"
        "💳 Тарифы — на 30 дней, оплата в пару кликов\n\n"
        "Выберите действие 👇"
    )


def account_status_text(status: AccountStatusView, free_daily_limit: int = 3) -> str:
    rows = ["📋 <b>Моя подписка</b>\n"]

    if status.vpn_subscription:
        sub = status.vpn_subscription
        rows.append(
            f"\n🌐 <b>Подключение</b>\n"
            f"Тариф: {escape(sub.plan.name)}\n"
            f"До: <b>{sub.expires_at.strftime('%d.%m.%Y')}</b> "
            f"({sub.days_left} дн.)\n"
            f"Устройств: {len(sub.devices)} / {sub.plan.device_limit}"
        )
    else:
        rows.append("\n🌐 <b>Подключение</b> — не активно")

    if status.has_ai_unlimited:
        if status.ai_subscription:
            sub = status.ai_subscription
            rows.append(
                f"\n\n💬 <b>AI-ассистент</b>\n"
                f"Тариф: {escape(sub.plan.name)}\n"
                f"До: <b>{sub.expires_at.strftime('%d.%m.%Y')}</b> "
                f"({sub.days_left} дн.)\n"
                "Сообщений: <b>без лимита</b>"
            )
        else:
            rows.append("\n\n💬 <b>AI-ассистент</b> — без лимита")
    else:
        rows.append(
            f"\n\n💬 <b>AI-ассистент</b> (бесплатно)\n"
            f"Сегодня осталось: <b>{status.ai_free_remaining}</b> "
            f"из {free_daily_limit}"
        )

    if not status.vpn_subscription and not status.has_ai_unlimited:
        rows.append("\n\n💡 Выберите «Тарифы» — Combo даёт всё в одном.")

    return "\n".join(rows)


def shop_text(plans: tuple[Plan, ...]) -> str:
    rows = [
        "💳 <b>Тарифы на 30 дней</b>\n",
        "Оплата тестовая (кнопка «Оплатить») — для проверки.\n",
    ]
    bundles = [p for p in plans if p.product_type == "bundle"]
    vpns = [p for p in plans if p.product_type == "vpn"]
    ais = [p for p in plans if p.product_type == "ai"]

    if bundles:
        rows.append("\n<b>🔥 Пакеты — подключение + AI</b>")
        for plan in bundles:
            hint = " ⭐ хит" if plan.slug == "combo" else ""
            rows.append(
                f"\n<b>{escape(plan.name)}</b>{hint} · {plan.price_rub} ₽\n"
                f"{escape(plan.description)}"
            )

    if vpns:
        rows.append("\n\n<b>🌐 Только подключение</b>")
        for plan in vpns:
            rows.append(
                f"\n<b>{escape(plan.name)}</b> · {plan.price_rub} ₽\n"
                f"{escape(plan.description)}"
            )

    if ais:
        rows.append("\n\n<b>💬 Только AI</b>")
        for plan in ais:
            rows.append(
                f"\n<b>{escape(plan.name)}</b> · {plan.price_rub} ₽\n"
                f"{escape(plan.description)}"
            )

    return "\n".join(rows)


def plan_details_text(plan: Plan) -> str:
    if plan.product_type == "bundle":
        body = (
            f"🔥 <b>{escape(plan.name)}</b>\n\n"
            f"{escape(plan.description)}\n\n"
            f"🌐 Устройств: <b>до {plan.device_limit}</b>\n"
            "💬 AI: <b>без лимита</b>\n"
            f"Срок: <b>{plan.duration_days} дней</b>\n"
            f"Цена: <b>{plan.price_rub} ₽</b>"
        )
    elif plan.product_type == "ai":
        body = (
            f"💬 <b>{escape(plan.name)}</b>\n\n"
            f"{escape(plan.description)}\n\n"
            f"Срок: <b>{plan.duration_days} дней</b>\n"
            f"Цена: <b>{plan.price_rub} ₽</b>"
        )
    else:
        body = (
            f"🌐 <b>{escape(plan.name)}</b>\n\n"
            f"{escape(plan.description)}\n\n"
            f"Устройств: <b>до {plan.device_limit}</b>\n"
            f"Срок: <b>{plan.duration_days} дней</b>\n"
            f"Цена: <b>{plan.price_rub} ₽</b>"
        )
    return body + "\n\nНажмите «Оплатить» — тариф активируется сразу."


def payment_success_text(subscription: SubscriptionView) -> str:
    expires = subscription.expires_at.strftime("%d.%m.%Y")
    if subscription.plan.product_type == "bundle":
        return (
            "✅ <b>Оплачено!</b>\n\n"
            f"Тариф: <b>{escape(subscription.plan.name)}</b>\n"
            f"До: <b>{expires}</b> ({subscription.days_left} дн.)\n\n"
            "🌐 «Подключение» → добавьте устройство и получите ключ.\n"
            "💬 «Чат с ассистентом» — AI без лимита."
        )
    if subscription.plan.product_type == "ai":
        return (
            "✅ <b>Оплачено!</b>\n\n"
            f"Тариф: <b>{escape(subscription.plan.name)}</b>\n"
            f"До: <b>{expires}</b> ({subscription.days_left} дн.)\n\n"
            "Откройте «Чат с ассистентом» и напишите сообщение."
        )
    return (
        "✅ <b>Оплачено!</b>\n\n"
        f"Тариф: <b>{escape(subscription.plan.name)}</b>\n"
        f"До: <b>{expires}</b> ({subscription.days_left} дн.)\n\n"
        "«Подключение» → «Мои ключи» → добавьте устройство."
    )


def vpn_menu_text() -> str:
    return (
        "🌐 <b>Подключение</b>\n\n"
        "1. Оплатите тариф с подключением (или Combo).\n"
        "2. «Мои ключи» — добавьте телефон или ноутбук.\n"
        "3. «Как подключить» — пошаговая инструкция.\n\n"
        "Нужна помощь — «Поддержка» в главном меню."
    )


def devices_text(subscription: SubscriptionView) -> str:
    expires_at = subscription.expires_at.strftime("%d.%m.%Y")
    rows = [
        "🔑 <b>Мои ключи</b>\n",
        f"Тариф: <b>{escape(subscription.plan.name)}</b>",
        f"Устройств: <b>{len(subscription.devices)}</b> "
        f"из <b>{subscription.plan.device_limit}</b>",
        f"До: <b>{expires_at}</b> ({subscription.days_left} дн.)",
    ]
    if not subscription.devices:
        rows.append("\n\nУстройств нет. Нажмите «Добавить устройство» 👇")
    else:
        rows.append("\n\n<b>Список:</b>")
        for device in subscription.devices:
            rows.append(f"\n{device.emoji} {escape(device.display_name)}")
        rows.append("\n\nНажмите устройство — скопируете ключ.")
    return "\n".join(rows)


def device_detail_text(device: DeviceView) -> str:
    return (
        f"{device.emoji} <b>{escape(device.display_name)}</b>\n\n"
        "🔑 <b>Ваш ключ</b>\n"
        f"<code>{escape(device.connection_uri)}</code>\n\n"
        "Скопируйте и вставьте в приложение (см. «Как подключить»)."
    )


def add_device_text(subscription: SubscriptionView) -> str:
    return (
        "➕ <b>Добавить устройство</b>\n\n"
        f"Можно ещё: <b>"
        f"{subscription.plan.device_limit - len(subscription.devices)}</b>\n\n"
        "Выберите тип — для каждого будет свой ключ."
    )


def no_subscription_text() -> str:
    return (
        "🔑 <b>Нет активного тарифа с подключением</b>\n\n"
        "Выберите тариф Combo или Connect в «Тарифы», "
        "затем добавьте устройство здесь."
    )


def activating_text() -> str:
    return "⏳ <b>Оплачиваем…</b>\n\nОбычно 2–3 секунды."


def adding_device_text() -> str:
    return "⏳ <b>Создаём ключ…</b>\n\nПодождите пару секунд."


def activation_error_text(error: str) -> str:
    return (
        "⚠️ <b>Не удалось выполнить</b>\n\n"
        f"{escape(error)}\n\n"
        "Попробуйте снова или «Поддержка»."
    )


def device_limit_exceeded_text() -> str:
    return (
        "⚠️ <b>Лимит устройств</b>\n\n"
        "Удалите одно устройство, чтобы добавить новое."
    )


def instructions_text() -> str:
    return (
        "📖 <b>Как подключить</b>\n\n"
        "1. «Мои ключи» → добавьте устройство → скопируйте ключ.\n"
        "2. Установите приложение на телефон или ПК.\n"
        "3. В приложении: «+» или «Импорт» → вставьте ключ.\n"
        "4. Включите подключение.\n\n"
        "<b>Приложения</b>\n\n"
        "📱 Android: "
        "<a href=\"https://play.google.com/store/apps/details?id=com.v2ray.ang\">v2rayNG</a>, "
        "<a href=\"https://play.google.com/store/apps/details?id=app.hiddify.com\">Hiddify</a>\n"
        "🍎 iPhone: "
        "<a href=\"https://apps.apple.com/app/streisand/id6450534064\">Streisand</a>, "
        "<a href=\"https://apps.apple.com/app/v2raytun/id6476628951\">v2RayTun</a>\n"
        "💻 ПК: "
        "<a href=\"https://github.com/hiddify/hiddify-app/releases\">Hiddify</a>\n\n"
        "Не работает — «Поддержка»."
    )


def support_text(contact: str) -> str:
    return (
        "🆘 <b>Поддержка</b>\n\n"
        f"Напишите: <b>{escape(contact)}</b>\n\n"
        "Поможем с оплатой, ключами и настройкой."
    )


def share_text(bot_username: str) -> str:
    return (
        "👥 <b>Поделиться</b>\n\n"
        "Отправьте ссылку другу — он откроет бота и сможет "
        "попробовать AI бесплатно.\n\n"
        f"Ссылка: https://t.me/{escape(bot_username)}"
    )


def ai_chat_intro_text(remaining: int, has_subscription: bool, free_daily_limit: int = 3) -> str:
    if has_subscription:
        quota = "💬 AI без лимита — подписка активна."
    else:
        quota = f"🆓 Бесплатно сегодня: <b>{remaining}</b> из {free_daily_limit}"
    return (
        "💬 <b>Чат с ассистентом</b>\n\n"
        f"{quota}\n\n"
        "Напишите сообщение — отвечу здесь.\n"
        "/stop — выйти из чата."
    )


def ai_quota_exceeded_text() -> str:
    return (
        "⛔ <b>Лимит на сегодня</b>\n\n"
        "Бесплатно — 3 сообщения в день.\n"
        "В «Тарифы» — Combo или Lite AI для безлимита."
    )


def ai_generating_text(frame: int) -> str:
    dots = "." * (frame % 3 + 1)
    return f"✨ <b>Думаю</b>{dots}"


def available_presets(subscription: SubscriptionView) -> tuple[DevicePreset, ...]:
    used = {device.slug for device in subscription.devices}
    return tuple(preset for preset in DEVICE_PRESETS if preset.slug not in used)
