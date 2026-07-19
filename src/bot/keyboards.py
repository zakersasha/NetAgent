from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.billing import AccountStatusView, SubscriptionView
from bot.plans import Plan, get_plan


def _plan(slug: str) -> Plan:
    return get_plan(slug)


def main_menu(*, allow_mock_payment: bool = False, bot_username: str = "") -> InlineKeyboardMarkup:
    standard = _plan("combo")
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Чат с ИИ", callback_data="ai:open")
    builder.button(
        text=f"⭐ {standard.name} · {standard.price_rub} ₽",
        callback_data="plan:combo",
    )
    if allow_mock_payment:
        connect = _plan("connect")
        builder.button(
            text=f"🧪 Тест без оплаты · {connect.name}",
            callback_data="mockpay:connect",
        )
    builder.button(text="📋 Моя подписка", callback_data="account")
    builder.button(text="💳 Все тарифы", callback_data="shop")
    if bot_username:
        builder.button(text="👥 Поделиться", callback_data="share")
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


def account_keyboard(status: AccountStatusView) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if status.vpn_subscription:
        builder.button(text="📖 Как подключить", callback_data="onboard:setup")
        if status.vpn_subscription.devices:
            builder.button(text="📋 Ключ текстом", callback_data="vpn:plain_key")
    else:
        standard = _plan("combo")
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
    if subscription.plan.product_type in ("vpn", "bundle"):
        builder.button(text="📖 Настроить VPN", callback_data="onboard:setup")
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


def payment_keyboard(
    plan: Plan,
    *,
    can_pay: bool = True,
    payment_provider: str = "mock",
    allow_mock_payment: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    is_yookassa = payment_provider.strip().lower() == "yookassa"
    if can_pay:
        if is_yookassa:
            builder.button(text=f"Оплатить {plan.price_rub} ₽", callback_data=f"pay:{plan.slug}")
        else:
            builder.button(text=f"Оплатить {plan.price_rub} ₽", callback_data=f"mockpay:{plan.slug}")
    if allow_mock_payment and is_yookassa:
        builder.button(text="🧪 Тест без оплаты", callback_data=f"mockpay:{plan.slug}")
    builder.button(text="💳 Другие тарифы", callback_data="shop")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def payment_link_keyboard(confirmation_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перейти к оплате", url=confirmation_url)
    builder.button(text="📋 Моя подписка", callback_data="account")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def subscription_reminder_keyboard(plan_slug: str, price_rub: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"💳 Продлить · {price_rub} ₽", callback_data=f"plan:{plan_slug}")
    builder.button(text="💳 Все тарифы", callback_data="shop")
    builder.adjust(1)
    return builder.as_markup()


def onboarding_step1_keyboard(*, privacy_url: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if privacy_url:
        builder.button(text="📄 Политика конфиденциальности", url=privacy_url)
    builder.button(text="Принять", callback_data="onboard:accept")
    builder.adjust(1)
    return builder.as_markup()


def onboarding_step2_plans_keyboard(plans: tuple[Plan, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        prefix = "⭐ " if plan.slug == "combo" else "🔒 "
        if plan.product_type == "bundle" and plan.slug != "combo":
            prefix = "✨ "
        builder.button(
            text=f"{prefix}{plan.name} · {plan.price_rub} ₽",
            callback_data=f"onboard:plan:{plan.slug}",
        )
    builder.button(text="← Назад", callback_data="onboard:back")
    builder.adjust(1)
    return builder.as_markup()


def onboarding_step2_pay_keyboard(
    plan: Plan,
    *,
    can_pay: bool = True,
    payment_provider: str = "mock",
    allow_mock_payment: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    is_yookassa = payment_provider.strip().lower() == "yookassa"
    if can_pay:
        if is_yookassa:
            builder.button(
                text=f"Оплатить {plan.price_rub} ₽",
                callback_data=f"onboard:pay:{plan.slug}",
            )
        else:
            builder.button(
                text=f"Оплатить {plan.price_rub} ₽",
                callback_data=f"onboard:mockpay:{plan.slug}",
            )
    if allow_mock_payment and is_yookassa:
        builder.button(
            text="🧪 Тест без оплаты",
            callback_data=f"onboard:mockpay:{plan.slug}",
        )
    builder.button(text="← К тарифам", callback_data="onboard:plans")
    builder.button(text="← Назад", callback_data="onboard:back")
    builder.adjust(1)
    return builder.as_markup()


def onboarding_step3_platform_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 iPhone", callback_data="onboard:platform:iphone")
    builder.button(text="🤖 Android", callback_data="onboard:platform:android")
    builder.button(text="💻 Компьютер", callback_data="onboard:platform:pc")
    builder.button(text="📋 Ключ текстом", callback_data="vpn:plain_key")
    builder.button(text="← Назад", callback_data="onboard:back")
    builder.adjust(1)
    return builder.as_markup()


def onboarding_step3_done_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Главное меню", callback_data="menu")
    builder.button(text="← Другое устройство", callback_data="onboard:platforms")
    builder.adjust(1)
    return builder.as_markup()


def onboarding_payment_link_keyboard(confirmation_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Перейти к оплате", url=confirmation_url)
    builder.button(text="✅ Я оплатил — настройка", callback_data="onboard:paid")
    builder.button(text="← К тарифам", callback_data="onboard:plans")
    builder.adjust(1)
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
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    return builder.as_markup()
