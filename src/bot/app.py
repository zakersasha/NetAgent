import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from bot.billing import MockBillingClient
from bot.handlers import create_router
from bot.settings import get_bot_settings


def create_bot(token: str, proxy_url: str) -> Bot:
    proxy = proxy_url.strip()
    session = AiohttpSession(proxy=proxy) if proxy else None
    return Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_bot_settings()
    token = settings.telegram_bot_token.strip()
    if not token or token == "mock-token":
        raise RuntimeError("Задайте TELEGRAM_BOT_TOKEN в файле .env (токен от @BotFather)")

    proxy = settings.bot_proxy_url.strip()
    if proxy:
        logging.info("Telegram API через прокси: %s", proxy.split("@")[-1])

    billing = MockBillingClient(
        public_host=settings.xray_public_host,
        timezone=settings.timezone,
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(create_router(settings, billing))

    bot = create_bot(token, proxy)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
