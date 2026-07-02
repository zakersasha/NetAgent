from html import escape

from bot.billing import AccountStatusView, DeviceView, SubscriptionView
from bot.plans import Plan, get_plan
from netagent_common.plans_display import marketing_for


def welcome_text(service_name: str) -> str:
    standard = get_plan("combo")
    return (
        f"👋 <b>{escape(service_name)}</b>\n\n"
        "Защищённый канал для удалённой работы и AI-помощник в Telegram.\n\n"
        "🆓 <b>3 сообщения AI</b> бесплатно сегодня\n"
        f"⭐ Рекомендуем тариф <b>{escape(standard.name)}</b> — "
        f"канал и AI, {standard.price_rub} ₽/мес\n\n"
        "Что делаем?"
    )


def account_status_text(status: AccountStatusView, free_daily_limit: int = 3) -> str:
    rows = ["📋 <b>Моя подписка</b>\n"]

    if status.vpn_subscription:
        sub = status.vpn_subscription
        m = marketing_for(sub.plan.slug)
        devices = f" · {m.devices}" if m else ""
        rows.append(
            f"\n🔒 <b>Защищённый канал</b> · активен\n"
            f"Тариф: {escape(sub.plan.name)}{devices}\n"
            f"До: <b>{sub.expires_at.strftime('%d.%m.%Y')}</b> "
            f"({sub.days_left} дн.)"
        )
        rows.append("\n\n" + instructions_short_text())
        if sub.devices:
            device = sub.devices[0]
            rows.append(
                f"\n\n📄 <b>Профиль доступа</b>\n"
                f"<code>{escape(device.connection_uri)}</code>"
            )
        else:
            rows.append(
                "\n\n📄 Профиль создаётся… Нажмите «Получить профиль» "
                "или подождите пару секунд."
            )
    else:
        rows.append("\n🔒 <b>Защищённый канал</b> · не активен")

    if status.has_ai_unlimited:
        if status.ai_subscription:
            sub = status.ai_subscription
            rows.append(
                f"\n\n💬 <b>AI-помощник</b> · без лимита\n"
                f"Тариф: {escape(sub.plan.name)}\n"
                f"До: <b>{sub.expires_at.strftime('%d.%m.%Y')}</b> "
                f"({sub.days_left} дн.)"
            )
        else:
            rows.append("\n\n💬 <b>AI-помощник</b> · без лимита")
    else:
        rows.append(
            f"\n\n💬 <b>AI-помощник</b> (бесплатно)\n"
            f"Сегодня: <b>{status.ai_free_remaining}</b> из {free_daily_limit}"
        )

    if not status.vpn_subscription:
        standard = get_plan("combo")
        rows.append(
            f"\n\n💡 Тариф «{escape(standard.name)}» — канал и AI, "
            f"{standard.description.lower()}."
        )

    return "\n".join(rows)


def instructions_short_text() -> str:
    return (
        "📖 <b>Как настроить</b>\n"
        "1. Скопируйте профиль доступа ниже.\n"
        "2. Импортируйте в клиентское приложение на устройстве.\n"
        "3. Включите соединение."
    )


def shop_text(plans: tuple[Plan, ...]) -> str:
    rows = [
        "💳 <b>Тарифы на 30 дней</b>\n",
        "Личный → Команда → Стандарт / Семья. Подробности — у каждого тарифа.\n",
    ]
    bundles = [p for p in plans if p.product_type == "bundle"]
    channels = [p for p in plans if p.product_type == "vpn"]
    ais = [p for p in plans if p.product_type == "ai"]

    if bundles:
        rows.append("\n<b>⭐ Канал и AI-помощник</b>")
        for plan in bundles:
            m = marketing_for(plan.slug)
            hint = " · рекомендуем" if plan.slug == "combo" else ""
            extra = f" · {m.devices}" if m else ""
            rows.append(
                f"\n<b>{escape(plan.name)}</b>{hint}{extra} · {plan.price_rub} ₽\n"
                f"{escape(plan.description)}"
            )

    if channels:
        rows.append("\n\n<b>🔒 Только защищённый канал</b>")
        for plan in channels:
            m = marketing_for(plan.slug)
            extra = f" · {m.devices}" if m else ""
            rows.append(
                f"\n<b>{escape(plan.name)}</b>{extra} · {plan.price_rub} ₽\n"
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
    m = marketing_for(plan.slug)
    devices = f"📱 <b>{m.devices}</b> · {m.audience}\n" if m and plan.product_type != "ai" else ""

    if plan.product_type == "bundle":
        body = (
            f"⭐ <b>{escape(plan.name)}</b>\n\n"
            f"{escape(plan.description)}\n\n"
            f"{devices}"
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
            f"🔒 <b>{escape(plan.name)}</b>\n\n"
            f"{escape(plan.description)}\n\n"
            f"{devices}"
            f"Срок: <b>{plan.duration_days} дней</b>\n"
            f"Цена: <b>{plan.price_rub} ₽</b>"
        )
    return (
        body
        + "\n\n✓ Активация сразу после оплаты\n"
        "✓ Профиль в «Моя подписка»\n"
        "✓ Поддержка в боте и на сайте"
    )


def payment_success_text(subscription: SubscriptionView) -> str:
    expires = subscription.expires_at.strftime("%d.%m.%Y")
    if subscription.plan.product_type == "bundle":
        return (
            "✅ <b>Готово!</b>\n\n"
            f"Тариф: <b>{escape(subscription.plan.name)}</b>\n"
            f"До: <b>{expires}</b> ({subscription.days_left} дн.)\n\n"
            "📋 «Моя подписка» — профиль доступа\n"
            "💬 «Попробовать AI» — помощник без лимита"
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
        "📋 «Моя подписка» — профиль доступа готов"
    )


def devices_text(subscription: SubscriptionView) -> str:
    expires_at = subscription.expires_at.strftime("%d.%m.%Y")
    m = marketing_for(subscription.plan.slug)
    devices = f" · {m.devices}" if m else ""
    rows = [
        "📄 <b>Профиль доступа</b>\n",
        f"Тариф: <b>{escape(subscription.plan.name)}</b>{devices}",
        f"До: <b>{expires_at}</b> ({subscription.days_left} дн.)",
    ]
    if not subscription.devices:
        rows.append("\n\nПрофиль ещё не создан. Нажмите «Получить профиль» 👇")
    else:
        device = subscription.devices[0]
        rows.append(
            f"\n\n<code>{escape(device.connection_uri)}</code>\n\n"
            "Используйте только на устройствах вашей подписки."
        )
    return "\n".join(rows)


def device_detail_text(device: DeviceView) -> str:
    return (
        f"{device.emoji} <b>{escape(device.display_name)}</b>\n\n"
        "📄 <b>Профиль доступа</b>\n"
        f"<code>{escape(device.connection_uri)}</code>\n\n"
        "Скопируйте и импортируйте в приложение."
    )


def regenerate_key_text() -> str:
    return (
        "🔄 <b>Новый профиль</b>\n\n"
        "Текущий профиль перестанет работать. "
        "Используйте, если доступ мог быть скомпрометирован."
    )


def no_subscription_text() -> str:
    standard = get_plan("combo")
    return (
        "📋 <b>Подписка не активна</b>\n\n"
        f"⭐ «{escape(standard.name)}» — {escape(standard.description)}, "
        f"{standard.price_rub} ₽/мес."
    )


def activating_text() -> str:
    return "⏳ <b>Оплачиваем…</b>\n\nОбычно 2–3 секунды."


def adding_device_text() -> str:
    return "⏳ <b>Создаём профиль…</b>\n\nПодождите пару секунд."


def activation_error_text(error: str) -> str:
    return (
        "⚠️ <b>Не удалось выполнить</b>\n\n"
        f"{escape(error)}\n\n"
        "Попробуйте снова или «Поддержка»."
    )


def device_limit_exceeded_text() -> str:
    return (
        "⚠️ <b>Лимит подписки</b>\n\n"
        "Достигнут предел использования по тарифу. Продлите подписку или выберите план с большим числом устройств."
    )


def instructions_text() -> str:
    return (
        "📖 <b>Как настроить доступ</b>\n\n"
        "1. «Моя подписка» → скопируйте профиль.\n"
        "2. Установите клиентское приложение на устройство.\n"
        "3. Импортируйте профиль и включите соединение.\n\n"
        "Не работает — «Поддержка» в боте или на сайте."
    )


def support_prompt_text() -> str:
    return (
        "🆘 <b>Поддержка</b>\n\n"
        "Выберите тему или опишите вопрос одним сообщением — "
        "мы ответим здесь в боте."
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
    if category in {"vpn", "access"}:
        topic = "🔒 Защищённый канал"
    elif category == "ai":
        topic = "💬 AI-помощник"
    elif category == "billing":
        topic = "💳 Оплата"
    else:
        topic = "📩 Общее"
    user_line = f"<code>{telegram_id}</code>" if telegram_id else "сайт"
    return (
        f"🆘 <b>Обращение #{ticket_id}</b>\n"
        f"Тема: {topic}\n"
        f"Пользователь: {user_line}\n\n"
        f"{escape(message)}"
    )


def share_text(bot_username: str) -> str:
    return (
        "👥 <b>Поделиться</b>\n\n"
        "Отправьте ссылку коллеге — он сможет "
        "попробовать AI бесплатно.\n\n"
        f"Ссылка: https://t.me/{escape(bot_username)}"
    )


def ai_chat_intro_text(remaining: int, has_subscription: bool, free_daily_limit: int = 3) -> str:
    if has_subscription:
        quota = "💬 AI без лимита — подписка активна."
    else:
        quota = f"🆓 Бесплатно сегодня: <b>{remaining}</b> из {free_daily_limit}"
    return (
        "💬 <b>Чат с AI-помощником</b>\n\n"
        f"{quota}\n\n"
        "Напишите сообщение — отвечу здесь.\n"
        "/stop — выйти из чата."
    )


def ai_quota_exceeded_text() -> str:
    standard = get_plan("combo")
    return (
        "⛔ <b>На сегодня бесплатные сообщения закончились</b>\n\n"
        f"Завтра снова 3 сообщения — или тариф «{escape(standard.name)}» "
        f"({standard.price_rub} ₽): AI без лимита и защищённый канал."
    )


def ai_generating_text(frame: int) -> str:
    dots = "." * (frame % 3 + 1)
    return f"✨ <b>Думаю</b>{dots}"
