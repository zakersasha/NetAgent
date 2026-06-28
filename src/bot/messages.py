from html import escape

from bot.billing import AccountStatusView, DeviceView, SubscriptionView
from bot.device_presets import DevicePreset, selectable_device_presets
from bot.plans import Plan


def welcome_text(service_name: str) -> str:
    return (
        f"👋 <b>{escape(service_name)}</b>\n\n"
        "Ваш умный помощник в Telegram: <b>чат с AI</b>, ответы на вопросы, "
        "идеи и подсказки на каждый день.\n\n"
        "🆓 <b>3 сообщения AI</b> бесплатно каждый день\n"
        "💬 Подписка — безлимитный чат с ассистентом\n"
        "🌐 Тарифы Combo — AI + стабильное подключение\n\n"
        "Выберите действие 👇"
    )


def account_status_text(status: AccountStatusView, free_daily_limit: int = 3) -> str:
    rows = ["📋 <b>Моя подписка</b>\n"]

    if status.vpn_subscription:
        sub = status.vpn_subscription
        rows.append(
            f"\n🌐 <b>Подключение</b> · активно\n"
            f"Тариф: {escape(sub.plan.name)}\n"
            f"До: <b>{sub.expires_at.strftime('%d.%m.%Y')}</b> "
            f"({sub.days_left} дн.)\n"
            f"Устройств: {len(sub.devices)} / {sub.plan.device_limit}"
        )
        rows.append("\n\n" + instructions_short_text())
        if sub.devices:
            for device in sub.devices:
                rows.append(
                    f"\n\n{device.emoji} <b>{escape(device.display_name)}</b>\n"
                    f"<code>{escape(device.connection_uri)}</code>"
                )
        else:
            rows.append(
                "\n\n🔑 Ключ появится после добавления устройства — "
                "кнопка «Добавить устройство» ниже."
            )
    else:
        rows.append("\n🌐 <b>Подключение</b> · не активно")

    if status.has_ai_unlimited:
        if status.ai_subscription:
            sub = status.ai_subscription
            rows.append(
                f"\n\n💬 <b>AI-ассистент</b> · без лимита\n"
                f"Тариф: {escape(sub.plan.name)}\n"
                f"До: <b>{sub.expires_at.strftime('%d.%m.%Y')}</b> "
                f"({sub.days_left} дн.)"
            )
        else:
            rows.append("\n\n💬 <b>AI-ассистент</b> · без лимита")
    else:
        rows.append(
            f"\n\n💬 <b>AI-ассистент</b> (бесплатно)\n"
            f"Сегодня: <b>{status.ai_free_remaining}</b> из {free_daily_limit}"
        )

    if not status.vpn_subscription:
        rows.append(
            "\n\n💡 Подписки нет — откройте «Тарифы» и выберите подходящий план."
        )

    return "\n".join(rows)


def instructions_short_text() -> str:
    return (
        "📖 <b>Как подключить</b>\n"
        "1. Скопируйте ключ ниже.\n"
        "2. Установите приложение (v2rayNG, Streisand, Hiddify).\n"
        "3. «Импорт» → вставьте ключ → включите."
    )


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
            "📋 «Моя подписка» — ключ и инструкция.\n"
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
        "📋 «Моя подписка» — добавьте устройство и скопируйте ключ."
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
        "Скопируйте и вставьте в приложение."
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
        "📋 <b>Подписка не активна</b>\n\n"
        "Выберите тариф в «Тарифы» — Combo даёт AI и подключение в одном."
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
        "1. «Моя подписка» → скопируйте ключ.\n"
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


def support_prompt_text() -> str:
    return (
        "🆘 <b>Поддержка</b>\n\n"
        "Выберите тему или просто напишите, что не работает — "
        "мы сохраним обращение и ответим."
    )


def support_received_text() -> str:
    return (
        "✅ <b>Обращение отправлено</b>\n\n"
        "Мы получили ваше сообщение и скоро ответим."
    )


def support_notify_text(
    ticket_id: int,
    telegram_id: int,
    category: str | None,
    message: str,
) -> str:
    if category == "vpn":
        topic = "🌐 Подключение"
    elif category == "ai":
        topic = "💬 AI-чат"
    else:
        topic = "📩 Без категории"
    return (
        f"🆘 <b>Обращение #{ticket_id}</b>\n"
        f"Тема: {topic}\n"
        f"Пользователь: <code>{telegram_id}</code>\n\n"
        f"{escape(message)}"
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
    return tuple(
        preset
        for preset in selectable_device_presets()
        if preset.slug not in used
    )
