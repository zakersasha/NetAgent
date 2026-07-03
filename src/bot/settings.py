from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = Field("", alias="TELEGRAM_BOT_TOKEN")
    bot_proxy_url: str = Field("", alias="BOT_PROXY_URL")
    payment_provider: str = Field("mock", alias="PAYMENT_PROVIDER")
    yookassa_shop_id: str = Field("", alias="YOOKASSA_SHOP_ID")
    yookassa_secret_key: str = Field("", alias="YOOKASSA_SECRET_KEY")
    yookassa_return_url: str = Field("", alias="YOOKASSA_RETURN_URL")
    service_name: str = Field("NetAgent", alias="BOT_SERVICE_NAME")
    support_contact: str = Field("@sashakharlamov", alias="BOT_SUPPORT_CONTACT")
    support_notify_telegram_id: int = Field(0, alias="SUPPORT_NOTIFY_TELEGRAM_ID")
    timezone: str = Field("Europe/Moscow", alias="TIMEZONE")
    xray_public_host: str = Field("45.93.137.80", alias="XRAY_PUBLIC_HOST")
    xray_public_port: int = Field(443, alias="XRAY_PUBLIC_PORT")

    vless_flow: str = Field("xtls-rprx-vision", alias="VLESS_FLOW")
    reality_sni: str = Field("www.wikipedia.org", alias="REALITY_SNI")
    reality_short_id: str = Field("6ba85179e30d4fc3", alias="REALITY_SHORT_ID")
    reality_public_key: str = Field("", alias="REALITY_PUBLIC_KEY")

    xray_agent_url: str = Field("", alias="XRAY_AGENT_URL")
    xray_agent_api_key: str = Field("", alias="XRAY_AGENT_API_KEY")
    xray_agent_verify_ssl: bool = Field(False, alias="XRAY_AGENT_VERIFY_SSL")
    xray_agent_timeout_seconds: float = Field(60.0, alias="XRAY_AGENT_TIMEOUT_SECONDS")
    database_url: str = Field("", alias="DATABASE_URL")

    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    openai_api_key_2: str = Field("", alias="OPENAI_API_KEY_2")
    openai_model: str = Field("gpt-4o-mini", alias="OPENAI_MODEL")
    openai_proxy_url: str = Field("", alias="OPENAI_PROXY_URL")
    openai_proxy_url_2: str = Field("", alias="OPENAI_PROXY_URL_2")
    bot_proxy_url_2: str = Field("", alias="BOT_PROXY_URL_2")
    ai_free_daily_limit: int = Field(3, alias="AI_FREE_DAILY_LIMIT")
    ai_system_prompt: str = Field(
        "Ты полезный AI-ассистент в Telegram. Отвечай коротко, по делу, на русском.",
        alias="AI_SYSTEM_PROMPT",
    )

    @field_validator("reality_public_key", mode="before")
    @classmethod
    def validate_reality_public_key(cls, value: object) -> str:
        normalized = str(value or "").strip()
        if normalized and len(normalized) == 16 and all(
            char in "0123456789abcdef" for char in normalized.lower()
        ):
            raise ValueError(
                "REALITY_PUBLIC_KEY — это pbk из vless://, не sid (16 hex)"
            )
        return normalized

    @field_validator("xray_agent_verify_ssl", mode="before")
    @classmethod
    def strip_bool_env(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().strip("\\")
        return value


@lru_cache
def get_bot_settings() -> BotSettings:
    return BotSettings()
