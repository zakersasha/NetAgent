from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = Field("", alias="TELEGRAM_BOT_TOKEN")
    bot_proxy_url: str = Field("", alias="BOT_PROXY_URL")
    payment_provider: str = Field("mock", alias="PAYMENT_PROVIDER")
    service_name: str = Field("NetAgent VPN", alias="BOT_SERVICE_NAME")
    support_contact: str = Field("Поддержка будет добавлена позже", alias="BOT_SUPPORT_CONTACT")
    timezone: str = Field("Europe/Moscow", alias="TIMEZONE")
    xray_public_host: str = Field("45.93.137.80", alias="XRAY_PUBLIC_HOST")


@lru_cache
def get_bot_settings() -> BotSettings:
    return BotSettings()
