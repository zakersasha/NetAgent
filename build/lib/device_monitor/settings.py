from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MonitorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field("", alias="DATABASE_URL")
    poll_interval_seconds: int = Field(30, alias="DEVICE_MONITOR_INTERVAL_SECONDS")
    max_online_ips: int = Field(1, alias="DEVICE_MONITOR_MAX_ONLINE_IPS")

    xray_agent_url: str = Field("", alias="XRAY_AGENT_URL")
    xray_agent_api_key: str = Field("", alias="XRAY_AGENT_API_KEY")
    xray_agent_verify_ssl: bool = Field(False, alias="XRAY_AGENT_VERIFY_SSL")
    xray_agent_timeout_seconds: float = Field(60.0, alias="XRAY_AGENT_TIMEOUT_SECONDS")

    geoip_database_path: str = Field("", alias="GEOIP_DATABASE_PATH")
    timezone: str = Field("Europe/Moscow", alias="TIMEZONE")


@lru_cache
def get_monitor_settings() -> MonitorSettings:
    return MonitorSettings()
