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
    "AI-ассистент в Telegram: задайте вопрос и получите ответ.\n"
    "3 сообщения бесплатно каждый день.\n"
    "Тарифы: безлимитный чат, Combo — AI + стабильное подключение.\n"
    "Поддержка: /support"
)

BOT_SHORT_DESCRIPTION = "AI-ассистент и подписки. Чат, тарифы, поддержка."


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(list(BOT_COMMANDS))
    await bot.set_my_description(BOT_DESCRIPTION)
    await bot.set_my_short_description(BOT_SHORT_DESCRIPTION)
