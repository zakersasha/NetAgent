import asyncio

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from bot.billing import (
    BillingClient,
    DeviceAlreadyExistsError,
    DeviceLimitExceededError,
    NoSubscriptionError,
)
from bot.keyboards import (
    back_to_menu_keyboard,
    device_detail_keyboard,
    device_presets_keyboard,
    devices_keyboard,
    main_menu,
    payment_keyboard,
    plans_keyboard,
)
from bot.messages import (
    activating_text,
    activation_error_text,
    add_device_text,
    adding_device_text,
    available_presets,
    device_detail_text,
    device_limit_exceeded_text,
    devices_text,
    instructions_text,
    no_subscription_text,
    payment_success_text,
    plan_details_text,
    plans_text,
    welcome_text,
)
from bot.plans import get_plan
from bot.settings import BotSettings


def create_router(settings: BotSettings, billing: BillingClient) -> Router:
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
        await callback.answer("Активирую тариф...")
        await callback.message.edit_text(activating_text(), reply_markup=None)

        try:
            subscription = await asyncio.to_thread(
                billing.activate_mock_payment,
                callback.from_user.id,
                plan_slug,
            )
        except RuntimeError as exc:
            await callback.message.edit_text(
                activation_error_text(str(exc)),
                reply_markup=main_menu(),
            )
            return

        await callback.message.edit_text(
            payment_success_text(subscription),
            reply_markup=devices_keyboard(subscription),
        )

    @router.callback_query(lambda query: query.data in {"my_key", "status"})
    async def my_key(callback: CallbackQuery) -> None:
        subscription = billing.get_subscription(callback.from_user.id)
        if not subscription:
            await callback.message.edit_text(no_subscription_text(), reply_markup=main_menu())
        else:
            await callback.message.edit_text(
                devices_text(subscription),
                reply_markup=devices_keyboard(subscription),
            )
        await callback.answer()

    @router.callback_query(lambda query: query.data == "device:add")
    async def add_device_menu(callback: CallbackQuery) -> None:
        subscription = billing.get_subscription(callback.from_user.id)
        if not subscription:
            await callback.message.edit_text(no_subscription_text(), reply_markup=main_menu())
            await callback.answer()
            return

        if len(subscription.devices) >= subscription.plan.device_limit:
            await callback.message.edit_text(
                device_limit_exceeded_text(),
                reply_markup=devices_keyboard(subscription),
            )
            await callback.answer()
            return

        presets = available_presets(subscription)
        if not presets:
            await callback.message.edit_text(
                device_limit_exceeded_text(),
                reply_markup=devices_keyboard(subscription),
            )
            await callback.answer()
            return

        await callback.message.edit_text(
            add_device_text(subscription),
            reply_markup=device_presets_keyboard(presets),
        )
        await callback.answer()

    @router.callback_query(lambda query: query.data and query.data.startswith("device:preset:"))
    async def add_device(callback: CallbackQuery) -> None:
        preset_slug = callback.data.split(":", 2)[2]
        await callback.answer("Добавляю устройство...")
        await callback.message.edit_text(adding_device_text(), reply_markup=None)

        try:
            await asyncio.to_thread(
                billing.add_device,
                callback.from_user.id,
                preset_slug,
            )
        except DeviceLimitExceededError:
            subscription = billing.get_subscription(callback.from_user.id)
            if subscription:
                await callback.message.edit_text(
                    device_limit_exceeded_text(),
                    reply_markup=devices_keyboard(subscription),
                )
            else:
                await callback.message.edit_text(
                    device_limit_exceeded_text(),
                    reply_markup=main_menu(),
                )
            return
        except (DeviceAlreadyExistsError, NoSubscriptionError, RuntimeError) as exc:
            await callback.message.edit_text(
                activation_error_text(str(exc)),
                reply_markup=main_menu(),
            )
            return

        subscription = billing.get_subscription(callback.from_user.id)
        if not subscription:
            await callback.message.edit_text(no_subscription_text(), reply_markup=main_menu())
            return

        await callback.message.edit_text(
            devices_text(subscription),
            reply_markup=devices_keyboard(subscription),
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
                await callback.message.edit_text(no_subscription_text(), reply_markup=main_menu())
            await callback.answer()
            return

        await callback.message.edit_text(
            device_detail_text(device),
            reply_markup=device_detail_keyboard(device_id),
        )
        await callback.answer()

    @router.callback_query(lambda query: query.data and query.data.startswith("device:remove:"))
    async def remove_device(callback: CallbackQuery) -> None:
        device_id = int(callback.data.split(":", 2)[2])
        try:
            await asyncio.to_thread(billing.remove_device, callback.from_user.id, device_id)
        except RuntimeError as exc:
            await callback.message.edit_text(
                activation_error_text(str(exc)),
                reply_markup=main_menu(),
            )
            return

        subscription = billing.get_subscription(callback.from_user.id)
        if not subscription:
            await callback.message.edit_text(no_subscription_text(), reply_markup=main_menu())
        else:
            await callback.message.edit_text(
                devices_text(subscription),
                reply_markup=devices_keyboard(subscription),
            )
        await callback.answer("Устройство удалено")

    @router.callback_query(lambda query: query.data == "instructions")
    async def instructions(callback: CallbackQuery) -> None:
        await callback.message.edit_text(
            instructions_text(),
            reply_markup=back_to_menu_keyboard(),
            disable_web_page_preview=True,
        )
        await callback.answer()

    return router
