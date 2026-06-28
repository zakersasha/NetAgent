from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.billing import AccountStatusView, SubscriptionView
from bot.device_presets import DevicePreset
from bot.messages import available_presets
from bot.plans import Plan


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Чат с ассистентом", callback_data="ai:open")
    builder.button(text="📋 Моя подписка", callback_data="account")
    builder.button(text="💳 Тарифы", callback_data="shop")
    builder.button(text="👥 Поделиться", callback_data="share")
    builder.button(text="🆘 Поддержка", callback_data="support")
    builder.adjust(1, 2, 2)
    return builder.as_markup()


def shop_keyboard(plans: tuple[Plan, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    bundles = [p for p in plans if p.product_type == "bundle"]
    vpns = [p for p in plans if p.product_type == "vpn"]
    ais = [p for p in plans if p.product_type == "ai"]

    for plan in bundles:
        badge = "🔥 " if plan.slug == "combo" else "⭐ "
        builder.button(
            text=f"{badge}{plan.name} · {plan.price_rub} ₽",
            callback_data=f"plan:{plan.slug}",
        )
    for plan in vpns:
        builder.button(
            text=f"🌐 {plan.name} · {plan.price_rub} ₽",
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


def account_keyboard(status: AccountStatusView) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    vpn = status.vpn_subscription
    if vpn:
        if len(vpn.devices) < vpn.plan.device_limit:
            builder.button(text="➕ Добавить устройство", callback_data="device:add")
        if vpn.devices:
            builder.button(text="🔑 Управление ключами", callback_data="my_key")
    else:
        builder.button(text="💳 Выбрать тариф", callback_data="shop")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def ai_chat_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Моя подписка", callback_data="account")
    builder.button(text="⬅️ Выйти из чата", callback_data="ai:leave")
    builder.adjust(2)
    return builder.as_markup()


def payment_keyboard(plan: Plan) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"✅ Оплатить {plan.price_rub} ₽", callback_data=f"mockpay:{plan.slug}")
    builder.button(text="💳 Другие тарифы", callback_data="shop")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def devices_keyboard(subscription: SubscriptionView) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for device in subscription.devices:
        builder.button(
            text=f"{device.emoji} {device.display_name}",
            callback_data=f"device:view:{device.id}",
        )

    if len(subscription.devices) < subscription.plan.device_limit:
        builder.button(text="➕ Добавить устройство", callback_data="device:add")

    builder.button(text="⬅️ Моя подписка", callback_data="account")
    builder.adjust(1)
    return builder.as_markup()


def device_presets_keyboard(presets: tuple[DevicePreset, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for preset in presets:
        builder.button(
            text=f"{preset.emoji} {preset.title}",
            callback_data=f"device:preset:{preset.slug}",
        )
    builder.button(text="⬅️ Назад", callback_data="account")
    builder.adjust(1)
    return builder.as_markup()


def device_detail_keyboard(device_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить устройство", callback_data=f"device:remove:{device_id}")
    builder.button(text="⬅️ К устройствам", callback_data="my_key")
    builder.button(text="⬅️ Моя подписка", callback_data="account")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    return builder.as_markup()


def support_category_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Проблема с подключением", callback_data="support:vpn")
    builder.button(text="💬 Проблема с AI-чатом", callback_data="support:ai")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def share_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    share_text = (
        f"Попробуй этого бота — AI-ассистент и полезные подписки: "
        f"https://t.me/{bot_username}"
    )
    builder.button(text="📨 Отправить другу", switch_inline_query=share_text)
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()
