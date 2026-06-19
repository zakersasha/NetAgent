import json
import subprocess
from typing import Any

from xray_agent.errors import ConfigError, XrayCommandError
from xray_agent.models import OnlineIpEntry, UserOnlineStats
from xray_agent.settings import AgentSettings


class XrayStatsService:
    def __init__(self, settings: AgentSettings) -> None:
        self.settings = settings

    def get_users_online(self) -> list[UserOnlineStats]:
        command = (
            f"{self.settings.xray_bin} api statsonlineiplist "
            f"-server={self.settings.xray_api_server} -all"
        )
        raw = self._run_command(command)
        payload = json.loads(raw)
        users = payload.get("users", [])
        if not isinstance(users, list):
            raise ConfigError("Unexpected Xray stats response: users is not a list")

        result: list[UserOnlineStats] = []
        for item in users:
            if not isinstance(item, dict):
                continue
            email = str(item.get("email", "")).strip()
            if not email:
                continue
            ips_raw = item.get("ips", [])
            ips: list[OnlineIpEntry] = []
            if isinstance(ips_raw, list):
                for ip_item in ips_raw:
                    if not isinstance(ip_item, dict):
                        continue
                    ip = str(ip_item.get("ip", "")).strip()
                    if not ip:
                        continue
                    last_seen = ip_item.get("lastSeen", ip_item.get("last_seen", 0))
                    ips.append(OnlineIpEntry(ip=ip, last_seen=int(last_seen or 0)))
            result.append(UserOnlineStats(email=email, ips=ips))
        return result

    def _run_command(self, command: str) -> str:
        completed = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=self.settings.command_timeout_seconds,
        )
        if completed.returncode != 0:
            output = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
            raise XrayCommandError(f"Command failed: {command}\n{output}")
        output = completed.stdout.strip()
        if not output:
            raise ConfigError("Xray stats API returned empty response")
        return output
