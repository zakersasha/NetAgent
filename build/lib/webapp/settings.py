from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    secret_key: str = Field("change-me-in-production", alias="WEB_SECRET_KEY")
    service_name: str = Field("NetAgent", alias="BOT_SERVICE_NAME")
    host: str = Field("0.0.0.0", alias="WEB_HOST")
    port: int = Field(8001, alias="WEB_PORT")
    database_url: str = Field("", alias="DATABASE_URL")
    timezone: str = Field("Europe/Moscow", alias="TIMEZONE")

    xray_public_host: str = Field("45.93.137.80", alias="XRAY_PUBLIC_HOST")
    xray_public_port: int = Field(443, alias="XRAY_PUBLIC_PORT")
    vless_flow: str = Field("xtls-rprx-vision", alias="VLESS_FLOW")
    reality_sni: str = Field("www.wikipedia.org", alias="REALITY_SNI")
    reality_short_id: str = Field("6ba85179e30d4fc2", alias="REALITY_SHORT_ID")
    reality_public_key: str = Field("", alias="REALITY_PUBLIC_KEY")

    xray_agent_url: str = Field("", alias="XRAY_AGENT_URL")
    xray_agent_api_key: str = Field("", alias="XRAY_AGENT_API_KEY")
    xray_agent_verify_ssl: bool = Field(False, alias="XRAY_AGENT_VERIFY_SSL")
    xray_agent_timeout_seconds: float = Field(60.0, alias="XRAY_AGENT_TIMEOUT_SECONDS")
    ai_free_daily_limit: int = Field(3, alias="AI_FREE_DAILY_LIMIT")


@lru_cache
def get_web_settings() -> WebSettings:
    return WebSettings()
