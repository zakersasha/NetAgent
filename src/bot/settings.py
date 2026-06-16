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

    vless_flow: str = Field("xtls-rprx-vision", alias="VLESS_FLOW")
    reality_sni: str = Field("www.wikipedia.org", alias="REALITY_SNI")
    reality_short_id: str = Field("6ba85179e30d4fc3", alias="REALITY_SHORT_ID")
    reality_public_key: str = Field("", alias="REALITY_PUBLIC_KEY")

    xray_agent_url: str = Field("", alias="XRAY_AGENT_URL")
    xray_agent_api_key: str = Field("", alias="XRAY_AGENT_API_KEY")
    xray_agent_verify_ssl: bool = Field(False, alias="XRAY_AGENT_VERIFY_SSL")


@lru_cache
def get_bot_settings() -> BotSettings:
    return BotSettings()
