import asyncio

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.billing import (
    BillingClient,
    BillingError,
    NoSubscriptionError,
)
from bot.keyboards import (
    account_keyboard,
    device_detail_keyboard,
    devices_keyboard,
    main_menu,
    payment_keyboard,
    payment_success_keyboard,
    share_keyboard,
    shop_keyboard,
)
from bot.messages import (
    account_status_text,
    activating_text,
    activation_error_text,
    adding_device_text,
    device_detail_text,
    devices_text,
    no_subscription_text,
    payment_success_text,
    plan_details_text,
    regenerate_key_text,
    share_text,
    shop_text,
    welcome_text,
)
from bot.settings import BotSettings


def create_router(settings: BotSettings, billing: BillingClient, bot_username: str) -> Router:
    router = Router(name="netagent_bot")

    @router.message(CommandStart())
    async def start(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(welcome_text(settings.service_name), reply_markup=main_menu())

    @router.message(Command("plans"))
    async def cmd_plans(message: Message) -> None:
        plans = billing.plans("shop")
        await message.answer(shop_text(plans), reply_markup=shop_keyboard(plans))

    @router.message(Command("devices"))
    async def cmd_devices(message: Message) -> None:
        subscription = billing.get_subscription(message.from_user.id)
        if not subscription:
            status = billing.get_account_status(message.from_user.id)
            await message.answer(
                no_subscription_text(),
                reply_markup=account_keyboard(status, bot_username),
            )
        else:
            await message.answer(
                devices_text(subscription),
                reply_markup=devices_keyboard(subscription),
            )

    @router.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        status = billing.get_account_status(message.from_user.id)
        await message.answer(
            account_status_text(status, settings.ai_free_daily_limit),
            reply_markup=account_keyboard(status, bot_username),
            disable_web_page_preview=True,
        )

    @router.callback_query(lambda query: query.data == "menu")
    async def menu(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await callback.message.edit_text(
            welcome_text(settings.service_name),
            reply_markup=main_menu(),
        )
        await callback.answer()

    @router.callback_query(lambda query: query.data == "account")
    async def account(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        status = billing.get_account_status(callback.from_user.id)
        await callback.message.edit_text(
            account_status_text(status, settings.ai_free_daily_limit),
            reply_markup=account_keyboard(status, bot_username),
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
        await callback.message.edit_text(plan_details_text(plan), reply_markup=payment_keyboard(plan))
        await callback.answer()

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
                reply_markup=main_menu(),
            )
            return

        await callback.message.edit_text(
            payment_success_text(subscription),
            reply_markup=payment_success_keyboard(subscription),
        )

    @router.callback_query(lambda query: query.data in {"my_key", "status"})
    async def my_key(callback: CallbackQuery) -> None:
        subscription = billing.get_subscription(callback.from_user.id)
        if not subscription:
            status = billing.get_account_status(callback.from_user.id)
            await callback.message.edit_text(
                no_subscription_text(),
                reply_markup=account_keyboard(status, bot_username),
            )
        else:
            await callback.message.edit_text(
                devices_text(subscription),
                reply_markup=devices_keyboard(subscription),
            )
        await callback.answer()

    @router.callback_query(lambda query: query.data == "device:ensure")
    async def ensure_key(callback: CallbackQuery) -> None:
        await callback.answer("Создаём ключ…")
        await callback.message.edit_text(adding_device_text(), reply_markup=None)
        try:
            await asyncio.to_thread(billing.ensure_vpn_key, callback.from_user.id)
        except (NoSubscriptionError, RuntimeError) as exc:
            await callback.message.edit_text(
                activation_error_text(str(exc)),
                reply_markup=main_menu(),
            )
            return
        status = billing.get_account_status(callback.from_user.id)
        await callback.message.edit_text(
            account_status_text(status, settings.ai_free_daily_limit),
            reply_markup=account_keyboard(status, bot_username),
        )

    @router.callback_query(lambda query: query.data == "device:regenerate")
    async def regenerate_key(callback: CallbackQuery) -> None:
        await callback.answer("Обновляем ключ…")
        await callback.message.edit_text(regenerate_key_text(), reply_markup=None)
        try:
            device = await asyncio.to_thread(billing.regenerate_vpn_key, callback.from_user.id)
        except (NoSubscriptionError, RuntimeError) as exc:
            await callback.message.edit_text(
                activation_error_text(str(exc)),
                reply_markup=main_menu(),
            )
            return
        await callback.message.edit_text(
            device_detail_text(device),
            reply_markup=device_detail_keyboard(device.id),
        )

    @router.callback_query(lambda query: query.data and query.data.startswith("device:view:"))
    async def view_device(callback: CallbackQuery) -> None:
        device_id = int(callback.data.split(":", 2)[2])
        device = billing.get_device(callback.from_user.id, device_id)
        if not device:
            subscription = billing.get_subscription(callback.from_user.id)
            if subscription:
                await callback.message.edit_text(
                    devices_text(subscription),
                    reply_markup=devices_keyboard(subscription),
                )
            else:
                status = billing.get_account_status(callback.from_user.id)
                await callback.message.edit_text(
                    no_subscription_text(),
                    reply_markup=account_keyboard(status, bot_username),
                )
            await callback.answer()
            return

        await callback.message.edit_text(
            device_detail_text(device),
            reply_markup=device_detail_keyboard(device_id),
        )
        await callback.answer()

    return router
