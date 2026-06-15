from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    xray_config_path: Path = Path("/usr/local/etc/xray/config.json")
    xray_inbound_tag: str = "vless-reality-in"
    xray_max_users: int = 50
    xray_reload_cmd: str = "systemctl restart xray"
    xray_test_cmd: str = "xray run -test -c {config_path}"
    xray_public_host: str = "45.93.137.80"

    agent_api_key: str = Field("change-me", min_length=8)
    agent_allowed_ips: set[str] = Field(default_factory=lambda: {"37.230.114.25"})
    agent_reserved_emails: set[str] = Field(default_factory=set)
    agent_reserved_uuids: set[str] = Field(default_factory=set)

    vless_flow: str = "xtls-rprx-vision"
    reality_sni: str = "www.wikipedia.org"
    reality_short_id: str = "6ba85179e30d4fc2"
    reality_fingerprint: str = "chrome"
    reality_public_key: str | None = None

    command_timeout_seconds: int = 20
    lock_timeout_seconds: int = 10

    @field_validator("agent_allowed_ips", "agent_reserved_emails", "agent_reserved_uuids", mode="before")
    @classmethod
    def split_csv_set(cls, value: str | set[str] | list[str] | None) -> set[str]:
        if value is None:
            return set()
        if isinstance(value, set):
            return {item.strip() for item in value if item.strip()}
        if isinstance(value, list):
            return {str(item).strip() for item in value if str(item).strip()}
        return {item.strip() for item in value.split(",") if item.strip()}


@lru_cache
def get_settings() -> AgentSettings:
    return AgentSettings()
