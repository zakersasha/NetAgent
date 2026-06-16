import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from xray_client.client import XrayAgentClient

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

    agent_url = settings.xray_agent_url.strip()
    xray_agent = None
    if agent_url:
        xray_agent = XrayAgentClient(
            base_url=agent_url,
            api_key=settings.xray_agent_api_key,
            verify_ssl=settings.xray_agent_verify_ssl,
            timeout_seconds=settings.xray_agent_timeout_seconds,
        )
        logging.info("Xray Agent: %s", agent_url)

    billing = MockBillingClient(
        public_host=settings.xray_public_host,
        timezone=settings.timezone,
        reality_public_key=settings.reality_public_key,
        reality_sni=settings.reality_sni,
        reality_short_id=settings.reality_short_id,
        vless_flow=settings.vless_flow,
        xray_agent=xray_agent,
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(create_router(settings, billing))

    bot = create_bot(token, proxy)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
