import asyncio

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.billing import BillingClient, BillingError, NoSubscriptionError
from bot.keyboards import (
    main_menu,
    onboarding_step1_keyboard,
    onboarding_step2_pay_keyboard,
    onboarding_step2_plans_keyboard,
    onboarding_step3_done_keyboard,
    onboarding_step3_platform_keyboard,
    onboarding_payment_link_keyboard,
)
from bot.messages import (
    activating_text,
    activation_error_text,
    onboarding_step1_text,
    onboarding_step2_plan_text,
    onboarding_step2_plans_text,
    onboarding_step3_platform_text,
    payment_checkout_text,
    welcome_text,
)
from bot.settings import BotSettings
from netagent_common.payment_service import PaymentService


class OnboardingStates(StatesGroup):
    wizard = State()


ONBOARD_TOTAL_STEPS = 3


def _vpn_shop_plans(billing: BillingClient):
    return tuple(
        p for p in billing.plans("shop") if p.product_type in ("vpn", "bundle")
    )


async def _set_step(state: FSMContext, step: int, **extra: object) -> None:
    data = {"onboard_step": step, **extra}
    await state.set_state(OnboardingStates.wizard)
    await state.update_data(**data)


async def _get_step(state: FSMContext) -> int:
    data = await state.get_data()
    return int(data.get("onboard_step", 1))


async def show_onboarding_step1(
    message_or_callback: Message | CallbackQuery,
    settings: BotSettings,
) -> None:
    text = onboarding_step1_text(settings.service_name)
    markup = onboarding_step1_keyboard()
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=markup)
    else:
        await message_or_callback.answer(text, reply_markup=markup)


async def show_onboarding_step2_plans(
    callback: CallbackQuery,
    billing: BillingClient,
) -> None:
    plans = _vpn_shop_plans(billing)
    await callback.message.edit_text(
        onboarding_step2_plans_text(plans),
        reply_markup=onboarding_step2_plans_keyboard(plans),
    )


async def show_onboarding_step2_plan(
    callback: CallbackQuery,
    billing: BillingClient,
    settings: BotSettings,
    plan_slug: str,
) -> None:
    plan = billing.get_plan(plan_slug)
    if not plan:
        await callback.answer("Тариф не найден", show_alert=True)
        return
    can_pay, blocked_reason = billing.can_purchase_plan(callback.from_user.id, plan_slug)
    await callback.message.edit_text(
        onboarding_step2_plan_text(plan, purchase_blocked=blocked_reason),
        reply_markup=onboarding_step2_pay_keyboard(
            plan,
            can_pay=can_pay,
            payment_provider=settings.payment_provider,
            allow_mock_payment=settings.allow_mock_payment,
        ),
    )


async def show_onboarding_step3_platforms(callback: CallbackQuery, billing: BillingClient) -> None:
    uri = await _connection_uri_for_user(billing, callback.from_user.id)
    await callback.message.edit_text(
        onboarding_step3_platform_text(uri),
        reply_markup=onboarding_step3_platform_keyboard(),
    )


async def show_onboarding_step3_instructions(
    callback: CallbackQuery,
    billing: BillingClient,
    platform: str,
) -> None:
    from bot.messages import onboarding_setup_instructions_text

    uri = await _connection_uri_for_user(billing, callback.from_user.id)
    await callback.message.edit_text(
        onboarding_setup_instructions_text(platform, uri),
        reply_markup=onboarding_step3_done_keyboard(),
        disable_web_page_preview=False,
    )


async def _connection_uri_for_user(billing: BillingClient, telegram_id: int) -> str | None:
    status = billing.get_account_status(telegram_id)
    if not status.vpn_subscription:
        return None
    if status.vpn_subscription.devices:
        return status.vpn_subscription.devices[0].connection_uri
    try:
        device = await asyncio.to_thread(billing.ensure_vpn_key, telegram_id)
    except (NoSubscriptionError, RuntimeError):
        return None
    return device.connection_uri


def create_onboarding_router(
    settings: BotSettings,
    billing: BillingClient,
    bot_username: str,
    payment_service: PaymentService | None,
) -> Router:
    router = Router(name="onboarding")

    def menu_markup():
        return main_menu(
            allow_mock_payment=settings.allow_mock_payment,
            bot_username=bot_username,
        )

    @router.message(CommandStart())
    async def start_onboarding(message: Message, state: FSMContext) -> None:
        await state.clear()
        if billing.get_subscription(message.from_user.id):
            await message.answer(
                welcome_text(settings.service_name),
                reply_markup=menu_markup(),
            )
            return
        await _set_step(state, 1)
        await show_onboarding_step1(message, settings)

    @router.callback_query(lambda q: q.data == "onboard:next")
    async def onboard_next(callback: CallbackQuery, state: FSMContext) -> None:
        step = await _get_step(state)
        if step == 1:
            await _set_step(state, 2)
            await show_onboarding_step2_plans(callback, billing)
        elif step == 2:
            subscription = billing.get_subscription(callback.from_user.id)
            if not subscription:
                await callback.answer("Сначала выберите и оплатите тариф", show_alert=True)
                return
            await _set_step(state, 3)
            await show_onboarding_step3_platforms(callback, billing)
        await callback.answer()

    @router.callback_query(lambda q: q.data == "onboard:back")
    async def onboard_back(callback: CallbackQuery, state: FSMContext) -> None:
        step = await _get_step(state)
        if step <= 1:
            await _set_step(state, 1)
            await show_onboarding_step1(callback, settings)
        elif step == 2:
            await _set_step(state, 1)
            await show_onboarding_step1(callback, settings)
        elif step == 3:
            await _set_step(state, 2)
            await show_onboarding_step2_plans(callback, billing)
        await callback.answer()

    @router.callback_query(lambda q: q.data == "onboard:plans")
    async def onboard_plans(callback: CallbackQuery, state: FSMContext) -> None:
        await _set_step(state, 2)
        await show_onboarding_step2_plans(callback, billing)
        await callback.answer()

    @router.callback_query(lambda q: q.data and q.data.startswith("onboard:plan:"))
    async def onboard_plan(callback: CallbackQuery, state: FSMContext) -> None:
        plan_slug = callback.data.split(":", 2)[2]
        await _set_step(state, 2, selected_plan=plan_slug)
        await show_onboarding_step2_plan(callback, billing, settings, plan_slug)
        await callback.answer()

    @router.callback_query(lambda q: q.data == "onboard:platforms")
    async def onboard_platforms(callback: CallbackQuery, state: FSMContext) -> None:
        await _set_step(state, 3)
        await show_onboarding_step3_platforms(callback, billing)
        await callback.answer()

    @router.callback_query(lambda q: q.data and q.data.startswith("onboard:platform:"))
    async def onboard_platform(callback: CallbackQuery, state: FSMContext) -> None:
        platform = callback.data.split(":", 2)[2]
        await _set_step(state, 3, platform=platform)
        await show_onboarding_step3_instructions(callback, billing, platform)
        await callback.answer()

    @router.callback_query(lambda q: q.data == "onboard:setup")
    async def onboard_setup_from_account(callback: CallbackQuery, state: FSMContext) -> None:
        if not billing.get_subscription(callback.from_user.id):
            await callback.answer("Нет активной подписки", show_alert=True)
            return
        await _set_step(state, 3)
        await show_onboarding_step3_platforms(callback, billing)
        await callback.answer()

    @router.callback_query(lambda q: q.data and q.data.startswith("onboard:mockpay:"))
    async def onboard_mockpay(callback: CallbackQuery, state: FSMContext) -> None:
        plan_slug = callback.data.split(":", 2)[2]
        await callback.answer("Оплачиваем…")
        await callback.message.edit_text(activating_text(), reply_markup=None)
        try:
            await asyncio.to_thread(
                billing.activate_mock_payment,
                callback.from_user.id,
                plan_slug,
            )
        except (BillingError, RuntimeError) as exc:
            await callback.message.edit_text(
                activation_error_text(str(exc)),
                reply_markup=onboarding_step2_pay_keyboard(
                    billing.get_plan(plan_slug),
                    can_pay=True,
                    payment_provider=settings.payment_provider,
                    allow_mock_payment=settings.allow_mock_payment,
                )
                if billing.get_plan(plan_slug)
                else onboarding_step2_plans_keyboard(_vpn_shop_plans(billing)),
            )
            return
        await _set_step(state, 3)
        await show_onboarding_step3_platforms(callback, billing)

    @router.callback_query(lambda q: q.data and q.data.startswith("onboard:pay:"))
    async def onboard_pay(callback: CallbackQuery, state: FSMContext) -> None:
        if not payment_service:
            await callback.answer("Оплата недоступна", show_alert=True)
            return
        plan_slug = callback.data.split(":", 2)[2]
        plan = billing.get_plan(plan_slug)
        if not plan:
            await callback.answer("Тариф не найден", show_alert=True)
            return
        await _set_step(state, 2, selected_plan=plan_slug, awaiting_payment=True)
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
                reply_markup=onboarding_step2_pay_keyboard(
                    plan,
                    can_pay=False,
                    payment_provider=settings.payment_provider,
                    allow_mock_payment=settings.allow_mock_payment,
                ),
            )
            return
        await callback.message.edit_text(
            payment_checkout_text(plan),
            reply_markup=onboarding_payment_link_keyboard(created.confirmation_url),
        )

    @router.callback_query(lambda q: q.data == "onboard:paid")
    async def onboard_paid(callback: CallbackQuery, state: FSMContext) -> None:
        if not billing.get_subscription(callback.from_user.id):
            await callback.answer("Оплата пока не поступила. Подождите и нажмите снова.", show_alert=True)
            return
        await _set_step(state, 3)
        await show_onboarding_step3_platforms(callback, billing)
        await callback.answer()

    return router
