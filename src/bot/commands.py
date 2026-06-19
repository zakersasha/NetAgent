from aiogram import Bot
from aiogram.types import BotCommand


BOT_COMMANDS: tuple[BotCommand, ...] = (
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="plans", description="Тарифы"),
    BotCommand(command="devices", description="Мои устройства"),
    BotCommand(command="help", description="Инструкции"),
    BotCommand(command="support", description="Поддержка"),
)


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(list(BOT_COMMANDS))
