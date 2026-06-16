import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.billing import MockBillingClient
from bot.handlers import create_router
from bot.settings import get_bot_settings


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_bot_settings()
    token = settings.telegram_bot_token.strip()
    if not token or token == "mock-token":
        raise RuntimeError("Задайте TELEGRAM_BOT_TOKEN в файле .env (токен от @BotFather)")

    billing = MockBillingClient(
        public_host=settings.xray_public_host,
        timezone=settings.timezone,
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(create_router(settings, billing))

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
