from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.billing import AccountStatusView, SubscriptionView
from bot.plans import Plan, get_plan


def _plan(slug: str) -> Plan:
    return get_plan(slug)


def main_menu() -> InlineKeyboardMarkup:
    standard = _plan("combo")
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Попробовать AI", callback_data="ai:open")
    builder.button(
        text=f"⭐ {standard.name} · {standard.price_rub} ₽",
        callback_data="plan:combo",
    )
    builder.button(text="📋 Моя подписка", callback_data="account")
    builder.button(text="💳 Все тарифы", callback_data="shop")
    builder.button(text="🆘 Поддержка", callback_data="support")
    builder.adjust(1)
    return builder.as_markup()


def shop_keyboard(plans: tuple[Plan, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    bundles = [p for p in plans if p.product_type == "bundle"]
    channels = [p for p in plans if p.product_type == "vpn"]
    ais = [p for p in plans if p.product_type == "ai"]

    for plan in bundles:
        prefix = "⭐ " if plan.slug == "combo" else "✨ "
        builder.button(
            text=f"{prefix}{plan.name} · {plan.price_rub} ₽",
            callback_data=f"plan:{plan.slug}",
        )
    for plan in channels:
        builder.button(
            text=f"🔒 {plan.name} · {plan.price_rub} ₽",
            callback_data=f"plan:{plan.slug}",
        )
    for plan in ais:
        builder.button(
            text=f"💬 {plan.name} · {plan.price_rub} ₽",
            callback_data=f"plan:{plan.slug}",
        )
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def upsell_keyboard() -> InlineKeyboardMarkup:
    standard = _plan("combo")
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"⭐ {standard.name} · {standard.price_rub} ₽",
        callback_data="plan:combo",
    )
    builder.button(text="💳 Все тарифы", callback_data="shop")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def account_keyboard(status: AccountStatusView, bot_username: str = "") -> InlineKeyboardMarkup:
    standard = _plan("combo")
    builder = InlineKeyboardBuilder()
    vpn = status.vpn_subscription
    if vpn:
        if not vpn.devices:
            builder.button(text="📄 Получить профиль", callback_data="device:ensure")
        else:
            builder.button(text="🔄 Новый профиль", callback_data="device:regenerate")
        if bot_username:
            builder.button(text="👥 Поделиться", callback_data="share")
    else:
        builder.button(
            text=f"⭐ {standard.name} · {standard.price_rub} ₽",
            callback_data="plan:combo",
        )
        builder.button(text="💳 Все тарифы", callback_data="shop")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def payment_success_keyboard(subscription: SubscriptionView) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if subscription.plan.product_type == "bundle":
        builder.button(text="📋 Моя подписка", callback_data="account")
        builder.button(text="💬 Начать чат", callback_data="ai:open")
    elif subscription.plan.product_type == "ai":
        builder.button(text="💬 Начать чат", callback_data="ai:open")
        builder.button(text="📋 Моя подписка", callback_data="account")
    else:
        builder.button(text="📋 Моя подписка", callback_data="account")
    builder.adjust(1)
    return builder.as_markup()


def ai_chat_keyboard() -> InlineKeyboardMarkup:
    standard = _plan("combo")
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Моя подписка", callback_data="account")
    builder.button(
        text=f"⭐ {standard.name} · {standard.price_rub} ₽",
        callback_data="plan:combo",
    )
    builder.button(text="⬅️ Выйти из чата", callback_data="ai:leave")
    builder.adjust(1, 1, 1)
    return builder.as_markup()


def payment_keyboard(plan: Plan) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Оплатить {plan.price_rub} ₽", callback_data=f"mockpay:{plan.slug}")
    builder.button(text="💳 Другие тарифы", callback_data="shop")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def devices_keyboard(subscription: SubscriptionView) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not subscription.devices:
        builder.button(text="📄 Получить профиль", callback_data="device:ensure")
    else:
        builder.button(text="🔄 Новый профиль", callback_data="device:regenerate")
    builder.button(text="⬅️ Моя подписка", callback_data="account")
    builder.adjust(1)
    return builder.as_markup()


def device_detail_keyboard(device_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Новый профиль", callback_data="device:regenerate")
    builder.button(text="⬅️ Моя подписка", callback_data="account")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    return builder.as_markup()


def support_category_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔒 Защищённый канал", callback_data="support:access")
    builder.button(text="💬 AI-помощник", callback_data="support:ai")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def share_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    share_text = (
        f"Сервис для удалённой работы и AI в Telegram: "
        f"https://t.me/{bot_username}"
    )
    builder.button(text="📨 Отправить", switch_inline_query=share_text)
    builder.button(text="⬅️ Моя подписка", callback_data="account")
    builder.adjust(1)
    return builder.as_markup()
