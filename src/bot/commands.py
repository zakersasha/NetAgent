from aiogram import Bot
from aiogram.types import BotCommand


BOT_COMMANDS: tuple[BotCommand, ...] = (
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="chat", description="AI-помощник"),
    BotCommand(command="plans", description="Тарифы"),
    BotCommand(command="devices", description="Профиль доступа"),
    BotCommand(command="help", description="Как настроить"),
    BotCommand(command="support", description="Поддержка"),
    BotCommand(command="stop", description="Выйти из чата"),
)

BOT_DESCRIPTION = (
    "Защищённый канал для удалённой работы и AI-помощник в Telegram.\n"
    "🆓 3 сообщения AI бесплатно каждый день.\n"
    "⭐ Тариф «Бизнес» — до 5 устройств + AI.\n"
    "Поддержка: /support"
)

BOT_SHORT_DESCRIPTION = "Защищённый канал и AI в Telegram. 3 msg бесплатно · Бизнес 299 ₽"


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(list(BOT_COMMANDS))
    await bot.set_my_description(BOT_DESCRIPTION)
    await bot.set_my_short_description(BOT_SHORT_DESCRIPTION)
