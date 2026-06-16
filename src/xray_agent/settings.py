from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _csv_to_set(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    xray_config_path: Path = Path("/usr/local/etc/xray/config.json")
    xray_inbound_tag: str = "vless-reality-in"
    xray_max_users: int = 50
    xray_reload_cmd: str = "systemctl restart xray"
    xray_test_cmd: str = "xray run -test -c {config_path}"
    xray_public_host: str = "45.93.137.80"

    agent_api_key: str = Field("change-me", min_length=8)
    # CSV в env: AGENT_ALLOWED_IPS=37.230.114.25
    agent_allowed_ips: str = Field(default="37.230.114.25")
    agent_reserved_emails: str = Field(default="")
    agent_reserved_uuids: str = Field(default="")

    vless_flow: str = "xtls-rprx-vision"
    reality_sni: str = "www.wikipedia.org"
    reality_short_id: str = "6ba85179e30d4fc2"
    reality_fingerprint: str = "chrome"
    reality_public_key: str | None = None

    command_timeout_seconds: int = 20
    lock_timeout_seconds: int = 10

    def allowed_ips(self) -> set[str]:
        return _csv_to_set(self.agent_allowed_ips)

    def reserved_emails(self) -> set[str]:
        return _csv_to_set(self.agent_reserved_emails)

    def reserved_uuids(self) -> set[str]:
        return _csv_to_set(self.agent_reserved_uuids)


@lru_cache
def get_settings() -> AgentSettings:
    return AgentSettings()
