from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.billing import SubscriptionView
from bot.device_presets import DevicePreset
from bot.messages import available_presets
from bot.plans import Plan

SUPPORT_URL = "https://t.me/sashakharlamov"


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Чат с AI", callback_data="ai:open")
    builder.button(text="⭐ AI Plus", callback_data="ai:plans")
    builder.button(text="🔐 Pro доступ", callback_data="pro:menu")
    builder.button(text="💬 Поддержка", url=SUPPORT_URL)
    builder.adjust(1, 2, 1)
    return builder.as_markup()


def pro_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 Мой ключ", callback_data="my_key")
    builder.button(text="📦 Тарифы Pro", callback_data="plans")
    builder.button(text="📖 Инструкции", callback_data="instructions")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1, 2, 1)
    return builder.as_markup()


def ai_chat_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ AI Plus", callback_data="ai:plans")
    builder.button(text="⬅️ Выйти из чата", callback_data="ai:leave")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1, 2)
    return builder.as_markup()


def ai_plans_keyboard(plans: tuple[Plan, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.button(
            text=f"⭐ {plan.name} · {plan.price_rub} ₽",
            callback_data=f"plan:{plan.slug}",
        )
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def plans_keyboard(plans: tuple[Plan, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.button(
            text=f"✨ {plan.name} · {plan.price_rub} ₽ · до {plan.device_limit} устр.",
            callback_data=f"plan:{plan.slug}",
        )
    builder.button(text="⬅️ Pro доступ", callback_data="pro:menu")
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard(plan: Plan) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"✅ Оплатить {plan.price_rub} ₽", callback_data=f"mockpay:{plan.slug}")
    if plan.product_type == "ai":
        builder.button(text="⭐ Другой тариф", callback_data="ai:plans")
    else:
        builder.button(text="📦 Другой тариф", callback_data="plans")
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

    builder.button(text="⬅️ Pro доступ", callback_data="pro:menu")
    builder.adjust(1)
    return builder.as_markup()


def device_presets_keyboard(presets: tuple[DevicePreset, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for preset in presets:
        builder.button(
            text=f"{preset.emoji} {preset.title}",
            callback_data=f"device:preset:{preset.slug}",
        )
    builder.button(text="⬅️ Назад", callback_data="my_key")
    builder.adjust(1)
    return builder.as_markup()


def device_detail_keyboard(device_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить устройство", callback_data=f"device:remove:{device_id}")
    builder.button(text="⬅️ К устройствам", callback_data="my_key")
    builder.button(text="⬅️ Pro доступ", callback_data="pro:menu")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    return builder.as_markup()


def support_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Написать в поддержку", url=SUPPORT_URL)
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()
