import logging

from aiogram import Bot, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.keyboards import main_menu, support_category_keyboard
from bot.messages import support_notify_text, support_prompt_text, support_received_text
from bot.settings import BotSettings
from bot.support_service import SupportService

logger = logging.getLogger(__name__)


class SupportStates(StatesGroup):
    waiting = State()


def create_support_router(settings: BotSettings, support_service: SupportService) -> Router:
    router = Router(name="support")

    async def _notify_admin(bot: Bot, ticket_id: int, telegram_id: int, category: str | None, message: str) -> None:
        notify_id = settings.support_notify_telegram_id
        if not notify_id:
            logger.warning("SUPPORT_NOTIFY_TELEGRAM_ID не задан — оповещение не отправлено")
            return
        try:
            await bot.send_message(
                chat_id=notify_id,
                text=support_notify_text(ticket_id, telegram_id, category, message),
            )
        except Exception:
            logger.exception("Не удалось отправить оповещение поддержки")

    async def _enter_support(message: Message, state: FSMContext) -> None:
        await state.set_state(SupportStates.waiting)
        await state.update_data(support_category=None)
        await message.answer(
            support_prompt_text(),
            reply_markup=support_category_keyboard(),
        )

    @router.message(Command("support"))
    async def cmd_support(message: Message, state: FSMContext) -> None:
        await _enter_support(message, state)

    @router.callback_query(lambda query: query.data == "support")
    async def support_open(callback: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(SupportStates.waiting)
        await state.update_data(support_category=None)
        await callback.message.edit_text(
            support_prompt_text(),
            reply_markup=support_category_keyboard(),
        )
        await callback.answer()

    @router.callback_query(
        StateFilter(SupportStates.waiting),
        lambda query: query.data in {"support:access", "support:vpn", "support:ai"},
    )
    async def support_category(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.data == "support:ai":
            category = "ai"
            label = "AI-помощник"
        else:
            category = "access"
            label = "защищённый канал"
        await state.update_data(support_category=category)
        await callback.message.edit_text(
            f"🆘 <b>Поддержка</b> · {label}\n\nОпишите вопрос одним сообщением 👇",
            reply_markup=support_category_keyboard(),
        )
        await callback.answer()

    @router.message(StateFilter(SupportStates.waiting))
    async def support_message(message: Message, state: FSMContext, bot: Bot) -> None:
        if not message.text or message.text.startswith("/"):
            await message.answer(
                "Напишите текст проблемы или нажмите «Главное меню».",
                reply_markup=support_category_keyboard(),
            )
            return

        data = await state.get_data()
        category = data.get("support_category")

        try:
            ticket = support_service.create_ticket(
                telegram_id=message.from_user.id,
                message=message.text,
                category=category,
            )
        except ValueError as exc:
            await message.answer(str(exc), reply_markup=support_category_keyboard())
            return

        await _notify_admin(bot, ticket.id, message.from_user.id, category, message.text)
        await state.clear()
        await message.answer(support_received_text(), reply_markup=main_menu(allow_mock_payment=settings.allow_mock_payment))

    return router
