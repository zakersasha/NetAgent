from aiogram import Bot
from aiogram.types import BotCommand


BOT_COMMANDS: tuple[BotCommand, ...] = (
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="chat", description="Чат с ассистентом"),
    BotCommand(command="plans", description="Тарифы"),
    BotCommand(command="devices", description="Мои ключи"),
    BotCommand(command="help", description="Как подключить"),
    BotCommand(command="support", description="Поддержка"),
    BotCommand(command="stop", description="Выйти из чата"),
)


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(list(BOT_COMMANDS))
