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

BOT_DESCRIPTION = (
    "AI-помощник + стабильное подключение в Telegram.\n"
    "🆓 3 сообщения AI бесплатно каждый день.\n"
    "⭐ Combo — интернет и AI за 299 ₽/мес.\n"
    "Поддержка: /support"
)

BOT_SHORT_DESCRIPTION = "AI и подключение в Telegram. 3 msg бесплатно · Combo 299 ₽"


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(list(BOT_COMMANDS))
    await bot.set_my_description(BOT_DESCRIPTION)
    await bot.set_my_short_description(BOT_SHORT_DESCRIPTION)
