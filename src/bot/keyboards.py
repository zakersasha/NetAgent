from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.plans import Plan


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Купить подписку", callback_data="plans")
    builder.button(text="Мой ключ", callback_data="my_key")
    builder.button(text="Статус", callback_data="status")
    builder.button(text="Поддержка", callback_data="support")
    builder.adjust(1)
    return builder.as_markup()


def plans_keyboard(plans: tuple[Plan, ...]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan in plans:
        builder.button(
            text=f"{plan.name} · {plan.price_rub} ₽ · {plan.device_limit} устр.",
            callback_data=f"plan:{plan.slug}",
        )
    builder.button(text="Назад", callback_data="menu")
    builder.adjust(1)
    return builder.as_markup()


def payment_keyboard(plan: Plan) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить (тест)", callback_data=f"mockpay:{plan.slug}")
    builder.button(text="Выбрать другой тариф", callback_data="plans")
    builder.adjust(1)
    return builder.as_markup()
