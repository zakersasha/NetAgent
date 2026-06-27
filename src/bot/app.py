import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage

from bot.ai_handlers import create_ai_router
from bot.ai_service import AiChatService
from bot.billing import BillingClient
from bot.commands import setup_bot_commands
from bot.handlers import create_router
from bot.settings import get_bot_settings
from netagent_common.openai_client import OpenAIChatClient
from netagent_common.proxy_urls import parse_proxy_urls, ProxyRotator
from netagent_db.session import create_session_factory
from xray_client.client import XrayAgentClient


def create_bot_session(proxy_url: str | None) -> AiohttpSession:
    if proxy_url:
        return AiohttpSession(proxy=proxy_url)
    return AiohttpSession()


async def create_bot_with_proxy_fallback(token: str, proxy_rotator: ProxyRotator) -> Bot:
    proxies = proxy_rotator.cycle()
    last_error: Exception | None = None
    for proxy in proxies:
        session = create_bot_session(proxy)
        bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
            session=session,
        )
        try:
            await bot.get_me()
            if proxy:
                logging.info("Telegram API через прокси: %s", proxy.split("@")[-1])
            return bot
        except Exception as exc:
            last_error = exc
            await bot.session.close()
    raise RuntimeError(f"Telegram API недоступен: {last_error}")


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_bot_settings()
    token = settings.telegram_bot_token.strip()
    if not token or token == "mock-token":
        raise RuntimeError("Задайте TELEGRAM_BOT_TOKEN в файле .env (токен от @BotFather)")

    database_url = settings.database_url.strip()
    if not database_url:
        raise RuntimeError("Задайте DATABASE_URL в .env")

    bot_proxy_rotator = ProxyRotator(
        parse_proxy_urls(settings.bot_proxy_url, settings.bot_proxy_url_2)
    )
    openai_proxy_rotator = ProxyRotator(
        parse_proxy_urls(
            settings.openai_proxy_url,
            settings.openai_proxy_url_2,
            settings.bot_proxy_url,
            settings.bot_proxy_url_2,
        )
    )

    openai_keys = tuple(
        key.strip()
        for key in (settings.openai_api_key, settings.openai_api_key_2)
        if key and key.strip()
    )
    if not openai_keys:
        raise RuntimeError("Задайте OPENAI_API_KEY в .env")

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

    session_factory = create_session_factory(database_url)
    billing = BillingClient(
        session_factory=session_factory,
        public_host=settings.xray_public_host,
        public_port=settings.xray_public_port,
        timezone=settings.timezone,
        reality_public_key=settings.reality_public_key,
        reality_sni=settings.reality_sni,
        reality_short_id=settings.reality_short_id,
        vless_flow=settings.vless_flow,
        xray_agent=xray_agent,
    )
    openai_client = OpenAIChatClient(
        api_keys=openai_keys,
        model=settings.openai_model,
        proxy_rotator=openai_proxy_rotator,
        system_prompt=settings.ai_system_prompt,
    )
    ai_service = AiChatService(
        session_factory=session_factory,
        openai_client=openai_client,
        timezone=settings.timezone,
        free_daily_limit=settings.ai_free_daily_limit,
    )

    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(create_ai_router(settings, billing, ai_service))
    dispatcher.include_router(create_router(settings, billing))

    bot = await create_bot_with_proxy_fallback(token, bot_proxy_rotator)
    await setup_bot_commands(bot)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
