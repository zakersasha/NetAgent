from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.plans import Plan


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Купить VPN", callback_data="plans")
    builder.button(text="🔑 Мой ключ", callback_data="my_key")
    builder.button(text="❓ Помощь", callback_data="support")
    builder.adjust(1, 2)
    return builder.as_markup()


def plans_keyboard(plans: tuple[Plan, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.button(
            text=f"💎 {plan.name} · {plan.price_rub} ₽ · до {plan.device_limit} устр.",
            callback_data=f"plan:{plan.slug}",
        )
    builder.button(text="⬅️ Назад", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard(plan: Plan) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"✅ Оплатить {plan.price_rub} ₽", callback_data=f"mockpay:{plan.slug}")
    builder.button(text="💎 Другой тариф", callback_data="plans")
    builder.button(text="⬅️ Главное меню", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()
