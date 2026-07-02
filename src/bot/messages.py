from html import escape

from bot.billing import AccountStatusView, DeviceView, SubscriptionView
from bot.plans import Plan
from netagent_common.traffic import format_traffic


def welcome_text(service_name: str) -> str:
    return (
        f"👋 <b>{escape(service_name)}</b>\n\n"
        "AI-помощник в Telegram + стабильное подключение в одной подписке.\n\n"
        "🆓 <b>3 сообщения AI</b> бесплатно сегодня\n"
        "⭐ <b>Combo</b> — интернет + AI без лимита · 299 ₽/мес\n\n"
        "Что делаем?"
    )


def account_status_text(status: AccountStatusView, free_daily_limit: int = 3) -> str:
    rows = ["📋 <b>Моя подписка</b>\n"]

    if status.vpn_subscription:
        sub = status.vpn_subscription
        traffic_line = ""
        if sub.traffic_limit_gb:
            traffic_line = (
                f"\nТрафик: <b>{format_traffic(sub.traffic_used_bytes, sub.traffic_limit_gb)}</b>"
            )
        rows.append(
            f"\n🌐 <b>Подключение</b> · активно\n"
            f"Тариф: {escape(sub.plan.name)}\n"
            f"До: <b>{sub.expires_at.strftime('%d.%m.%Y')}</b> "
            f"({sub.days_left} дн.)"
            f"{traffic_line}"
        )
        rows.append("\n\n" + instructions_short_text())
        if sub.devices:
            device = sub.devices[0]
            rows.append(
                f"\n\n🔑 <b>Ключ подключения</b>\n"
                f"<code>{escape(device.connection_uri)}</code>"
            )
        else:
            rows.append(
                "\n\n🔑 Ключ создаётся… Нажмите «Получить ключ» "
                "или подождите пару секунд."
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
            "\n\n💡 Подключите <b>Combo</b> — интернет и AI в одном тарифе."
        )

    return "\n".join(rows)


def instructions_short_text() -> str:
    return (
        "📖 <b>Как подключить</b>\n"
        "1. Скопируйте ключ ниже.\n"
        "2. Установите v2rayNG, Streisand или Hiddify.\n"
        "3. «Импорт» → вставьте ключ → включите."
    )


def shop_text(plans: tuple[Plan, ...]) -> str:
    rows = [
        "💳 <b>Тарифы на 30 дней</b>\n",
        "Combo — лучший выбор: интернет + AI выгоднее, чем по отдельности.\n",
    ]
    bundles = [p for p in plans if p.product_type == "bundle"]
    vpns = [p for p in plans if p.product_type == "vpn"]
    ais = [p for p in plans if p.product_type == "ai"]

    if bundles:
        rows.append("\n<b>⭐ Пакеты — подключение + AI</b>")
        for plan in bundles:
            hint = " · рекомендуем" if plan.slug == "combo" else ""
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
        traffic = (
            f"📊 Трафик: <b>{plan.traffic_limit_gb} ГБ/мес</b>\n" if plan.traffic_limit_gb else ""
        )
        body = (
            f"⭐ <b>{escape(plan.name)}</b>\n\n"
            f"{escape(plan.description)}\n\n"
            f"{traffic}"
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
            f"📊 Трафик: <b>{plan.traffic_limit_gb} ГБ/мес</b>\n"
            f"Срок: <b>{plan.duration_days} дней</b>\n"
            f"Цена: <b>{plan.price_rub} ₽</b>"
        )
    return (
        body
        + "\n\n✓ Активация сразу после оплаты\n"
        "✓ Ключ в «Моя подписка»\n"
        "✓ Поддержка в этом чате"
    )


def payment_success_text(subscription: SubscriptionView) -> str:
    expires = subscription.expires_at.strftime("%d.%m.%Y")
    if subscription.plan.product_type == "bundle":
        return (
            "✅ <b>Готово!</b>\n\n"
            f"Тариф: <b>{escape(subscription.plan.name)}</b>\n"
            f"До: <b>{expires}</b> ({subscription.days_left} дн.)\n\n"
            "🔑 Ключ уже в «Моя подписка»\n"
            "💬 AI без лимита — напишите сообщение прямо сейчас"
        )
    if subscription.plan.product_type == "ai":
        return (
            "✅ <b>Готово!</b>\n\n"
            f"Тариф: <b>{escape(subscription.plan.name)}</b>\n"
            f"До: <b>{expires}</b> ({subscription.days_left} дн.)\n\n"
            "💬 Нажмите «Начать чат» и напишите сообщение."
        )
    return (
        "✅ <b>Готово!</b>\n\n"
        f"Тариф: <b>{escape(subscription.plan.name)}</b>\n"
        f"До: <b>{expires}</b> ({subscription.days_left} дн.)\n\n"
        "🔑 Ключ уже в «Моя подписка»"
    )


def devices_text(subscription: SubscriptionView) -> str:
    expires_at = subscription.expires_at.strftime("%d.%m.%Y")
    traffic = ""
    if subscription.traffic_limit_gb:
        traffic = (
            f"Трафик: <b>{format_traffic(subscription.traffic_used_bytes, subscription.traffic_limit_gb)}</b>\n"
        )
    rows = [
        "🔑 <b>Ключ подключения</b>\n",
        f"Тариф: <b>{escape(subscription.plan.name)}</b>",
        traffic + f"До: <b>{expires_at}</b> ({subscription.days_left} дн.)",
    ]
    if not subscription.devices:
        rows.append("\n\nКлюч ещё не создан. Нажмите «Получить ключ» 👇")
    else:
        device = subscription.devices[0]
        rows.append(
            f"\n\n<code>{escape(device.connection_uri)}</code>\n\n"
            "Не делитесь ключом — трафик общий на всех, кто им пользуется."
        )
    return "\n".join(rows)


def device_detail_text(device: DeviceView) -> str:
    return (
        f"{device.emoji} <b>{escape(device.display_name)}</b>\n\n"
        "🔑 <b>Ключ подключения</b>\n"
        f"<code>{escape(device.connection_uri)}</code>\n\n"
        "Скопируйте и вставьте в приложение."
    )


def regenerate_key_text() -> str:
    return (
        "🔄 <b>Новый ключ</b>\n\n"
        "Старый ключ перестанет работать. "
        "Используйте, если ключ могли скопировать."
    )


def no_subscription_text() -> str:
    return (
        "📋 <b>Подписка не активна</b>\n\n"
        "⭐ <b>Combo</b> — интернет и AI в одном тарифе.\n"
        "Нажмите «Подключить Combo» или выберите другой план."
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
        "⚠️ <b>Лимит трафика</b>\n\n"
        "Месячный лимит исчерпан. Продлите тариф или выберите план с большим объёмом."
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
        "Выберите тему или напишите, что не работает — "
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
        "Отправьте ссылку другу — он сможет "
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
        "⛔ <b>На сегодня бесплатные сообщения закончились</b>\n\n"
        "Завтра снова 3 сообщения — или подключите Combo:\n"
        "• AI без лимита\n"
        "• + стабильный интернет"
    )


def ai_generating_text(frame: int) -> str:
    dots = "." * (frame % 3 + 1)
    return f"✨ <b>Думаю</b>{dots}"
