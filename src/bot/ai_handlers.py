import asyncio
import html

from aiogram import Router
from aiogram.enums import ChatAction
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.ai_service import AiChatService, AiQuotaExceededError
from bot.billing import BillingClient
from bot.keyboards import ai_chat_keyboard, ai_plans_keyboard, main_menu
from bot.messages import ai_chat_intro_text, ai_generating_text, ai_quota_exceeded_text, activation_error_text
from bot.settings import BotSettings


class AiChatStates(StatesGroup):
    active = State()


def create_ai_router(
    settings: BotSettings,
    billing: BillingClient,
    ai_service: AiChatService,
) -> Router:
    router = Router(name="ai_chat")

    async def _enter_chat(message: Message, state: FSMContext) -> None:
        has_sub = ai_service.has_ai_subscription(message.from_user.id)
        remaining = ai_service.remaining_free_messages(message.from_user.id)
        await state.set_state(AiChatStates.active)
        await message.answer(
            ai_chat_intro_text(remaining, has_sub),
            reply_markup=ai_chat_keyboard(),
        )

    @router.message(Command("chat"))
    async def cmd_chat(message: Message, state: FSMContext) -> None:
        await _enter_chat(message, state)

    @router.message(Command("stop"), StateFilter(AiChatStates.active))
    async def cmd_stop(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Чат завершён.", reply_markup=main_menu())

    @router.callback_query(lambda query: query.data == "ai:open")
    async def open_chat(callback: CallbackQuery, state: FSMContext) -> None:
        has_sub = ai_service.has_ai_subscription(callback.from_user.id)
        remaining = ai_service.remaining_free_messages(callback.from_user.id)
        await state.set_state(AiChatStates.active)
        await callback.message.edit_text(
            ai_chat_intro_text(remaining, has_sub),
            reply_markup=ai_chat_keyboard(),
        )
        await callback.answer()

    @router.callback_query(lambda query: query.data == "ai:leave")
    async def leave_chat(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await callback.message.edit_text("Чат завершён.", reply_markup=main_menu())
        await callback.answer()

    @router.callback_query(lambda query: query.data == "ai:plans")
    async def show_ai_plans(callback: CallbackQuery) -> None:
        from bot.messages import plans_text

        plans = billing.plans("ai")
        await callback.message.edit_text(
            plans_text(plans, title="⭐ <b>Тарифы AI</b>"),
            reply_markup=ai_plans_keyboard(plans),
        )
        await callback.answer()

    @router.message(StateFilter(AiChatStates.active))
    async def chat_message(message: Message, state: FSMContext) -> None:
        if not message.text or message.text.startswith("/"):
            await message.answer(
                "Напишите текстовое сообщение или /stop для выхода.",
                reply_markup=ai_chat_keyboard(),
            )
            return

        status = await message.answer(ai_generating_text(0))
        stop_event = asyncio.Event()

        async def animate() -> None:
            frame = 0
            while not stop_event.is_set():
                await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
                try:
                    await status.edit_text(ai_generating_text(frame))
                except Exception:
                    pass
                frame += 1
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=0.9)
                except TimeoutError:
                    continue

        animation_task = asyncio.create_task(animate())
        try:
            response = await asyncio.to_thread(
                ai_service.complete_message,
                message.from_user.id,
                message.text,
            )
        except AiQuotaExceededError:
            stop_event.set()
            await animation_task
            await status.edit_text(ai_quota_exceeded_text(), reply_markup=ai_chat_keyboard())
            return
        except RuntimeError as exc:
            stop_event.set()
            await animation_task
            await status.edit_text(
                activation_error_text(str(exc)),
                reply_markup=ai_chat_keyboard(),
            )
            return

        stop_event.set()
        await animation_task

        safe_text = html.escape(response)
        if len(safe_text) > 4000:
            safe_text = safe_text[:3997] + "..."
        await status.edit_text(safe_text, reply_markup=ai_chat_keyboard())

    return router
