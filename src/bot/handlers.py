from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.billing import MockBillingClient
from bot.keyboards import main_menu, payment_keyboard, plans_keyboard
from bot.messages import (
    no_subscription_text,
    plan_details_text,
    plans_text,
    subscription_text,
    welcome_text,
)
from bot.plans import get_plan
from bot.settings import BotSettings


def create_router(settings: BotSettings, billing: MockBillingClient) -> Router:
    router = Router(name="netagent_bot")

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        await message.answer(welcome_text(settings.service_name), reply_markup=main_menu())

    @router.callback_query(lambda query: query.data == "menu")
    async def menu(callback: CallbackQuery) -> None:
        await callback.message.edit_text(
            welcome_text(settings.service_name),
            reply_markup=main_menu(),
        )
        await callback.answer()

    @router.callback_query(lambda query: query.data == "plans")
    async def show_plans(callback: CallbackQuery) -> None:
        plans = billing.plans()
        await callback.message.edit_text(plans_text(plans), reply_markup=plans_keyboard(plans))
        await callback.answer()

    @router.callback_query(lambda query: query.data and query.data.startswith("plan:"))
    async def show_plan(callback: CallbackQuery) -> None:
        plan_slug = callback.data.split(":", 1)[1]
        plan = get_plan(plan_slug)
        await callback.message.edit_text(plan_details_text(plan), reply_markup=payment_keyboard(plan))
        await callback.answer()

    @router.callback_query(lambda query: query.data and query.data.startswith("mockpay:"))
    async def mock_payment(callback: CallbackQuery) -> None:
        plan_slug = callback.data.split(":", 1)[1]
        subscription = billing.activate_mock_payment(callback.from_user.id, plan_slug)
        await callback.message.edit_text(
            subscription_text(subscription),
            reply_markup=main_menu(),
            parse_mode="Markdown",
        )
        await callback.answer("Тестовая оплата прошла")

    @router.callback_query(lambda query: query.data in {"my_key", "status"})
    async def status(callback: CallbackQuery) -> None:
        subscription = billing.get_subscription(callback.from_user.id)
        if not subscription:
            await callback.message.edit_text(no_subscription_text(), reply_markup=main_menu())
        else:
            await callback.message.edit_text(
                subscription_text(subscription),
                reply_markup=main_menu(),
                parse_mode="Markdown",
            )
        await callback.answer()

    @router.callback_query(lambda query: query.data == "support")
    async def support(callback: CallbackQuery) -> None:
        await callback.message.edit_text(settings.support_contact, reply_markup=main_menu())
        await callback.answer()

    return router
