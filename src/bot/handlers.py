import asyncio

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.billing import (
    BillingClient,
    BillingError,
)
from bot.keyboards import (
    account_keyboard,
    main_menu,
    payment_keyboard,
    payment_link_keyboard,
    payment_success_keyboard,
    share_keyboard,
    shop_keyboard,
)
from bot.messages import (
    account_status_text,
    activating_text,
    activation_error_text,
    no_subscription_text,
    payment_checkout_text,
    payment_success_text,
    plan_details_text,
    share_text,
    shop_text,
    welcome_text,
)
from bot.settings import BotSettings
from netagent_common.payment_service import PaymentService


def create_router(
    settings: BotSettings,
    billing: BillingClient,
    bot_username: str,
    payment_service: PaymentService | None = None,
) -> Router:
    router = Router(name="netagent_bot")

    def menu_markup():
        return main_menu(
            allow_mock_payment=settings.allow_mock_payment,
            bot_username=bot_username,
        )

    @router.message(CommandStart())
    async def start_existing_user(message: Message, state: FSMContext) -> None:
        if not billing.get_subscription(message.from_user.id):
            return
        await state.clear()
        await message.answer(welcome_text(settings.service_name), reply_markup=menu_markup())

    @router.message(Command("plans"))
    async def cmd_plans(message: Message) -> None:
        plans = billing.plans("shop")
        await message.answer(shop_text(plans), reply_markup=shop_keyboard(plans))

    @router.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        status = billing.get_account_status(message.from_user.id)
        await message.answer(
            account_status_text(status, settings.ai_free_daily_limit),
            reply_markup=account_keyboard(status),
            disable_web_page_preview=True,
        )

    @router.callback_query(lambda query: query.data == "menu")
    async def menu(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await callback.message.edit_text(
            welcome_text(settings.service_name),
            reply_markup=menu_markup(),
        )
        await callback.answer()

    @router.callback_query(lambda query: query.data == "account")
    async def account(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        status = billing.get_account_status(callback.from_user.id)
        await callback.message.edit_text(
            account_status_text(status, settings.ai_free_daily_limit),
            reply_markup=account_keyboard(status),
            disable_web_page_preview=True,
        )
        await callback.answer()

    @router.callback_query(lambda query: query.data == "shop")
    async def shop(callback: CallbackQuery) -> None:
        plans = billing.plans("shop")
        await callback.message.edit_text(shop_text(plans), reply_markup=shop_keyboard(plans))
        await callback.answer()

    @router.callback_query(lambda query: query.data == "share")
    async def share(callback: CallbackQuery) -> None:
        await callback.message.edit_text(
            share_text(bot_username),
            reply_markup=share_keyboard(bot_username),
        )
        await callback.answer()

    @router.callback_query(lambda query: query.data and query.data.startswith("plan:"))
    async def show_plan(callback: CallbackQuery) -> None:
        plan_slug = callback.data.split(":", 1)[1]
        plan = billing.get_plan(plan_slug)
        if not plan:
            await callback.answer("Тариф не найден", show_alert=True)
            return
        can_pay, blocked_reason = billing.can_purchase_plan(callback.from_user.id, plan_slug)
        await callback.message.edit_text(
            plan_details_text(plan, purchase_blocked=blocked_reason),
            reply_markup=payment_keyboard(
                plan,
                can_pay=can_pay,
                payment_provider=settings.payment_provider,
                allow_mock_payment=settings.allow_mock_payment,
            ),
        )
        await callback.answer()

    @router.callback_query(lambda query: query.data and query.data.startswith("pay:"))
    async def yookassa_payment(callback: CallbackQuery) -> None:
        if not payment_service:
            await callback.answer("Оплата недоступна", show_alert=True)
            return

        plan_slug = callback.data.split(":", 1)[1]
        plan = billing.get_plan(plan_slug)
        if not plan:
            await callback.answer("Тариф не найден", show_alert=True)
            return

        await callback.answer("Создаём счёт…")
        await callback.message.edit_text(activating_text(), reply_markup=None)

        try:
            created = await asyncio.to_thread(
                payment_service.create_bot_payment,
                callback.from_user.id,
                plan_slug,
            )
        except BillingError as exc:
            await callback.message.edit_text(
                activation_error_text(str(exc)),
                reply_markup=menu_markup(),
            )
            return

        await callback.message.edit_text(
            payment_checkout_text(plan),
            reply_markup=payment_link_keyboard(created.confirmation_url),
        )

    @router.callback_query(lambda query: query.data and query.data.startswith("mockpay:"))
    async def mock_payment(callback: CallbackQuery) -> None:
        plan_slug = callback.data.split(":", 1)[1]
        await callback.answer("Оплачиваем…")
        await callback.message.edit_text(activating_text(), reply_markup=None)

        try:
            subscription = await asyncio.to_thread(
                billing.activate_mock_payment,
                callback.from_user.id,
                plan_slug,
            )
        except (BillingError, RuntimeError) as exc:
            await callback.message.edit_text(
                activation_error_text(str(exc)),
                reply_markup=menu_markup(),
            )
            return

        await callback.message.edit_text(
            payment_success_text(subscription),
            reply_markup=payment_success_keyboard(subscription),
        )

    return router
