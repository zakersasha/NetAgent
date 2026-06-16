import json
import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from xray_agent.errors import (
    ConfigError,
    ReservedUserError,
    UserLimitReached,
    UserNotFound,
    XrayCommandError,
)
from xray_agent.models import AddUserRequest, CountResponse, UserResponse
from xray_agent.settings import AgentSettings
from netagent_common.vless_uri import build_vless_reality_uri


class XrayConfigService:
    def __init__(self, settings: AgentSettings) -> None:
        self.settings = settings
        self.config_path = settings.xray_config_path
        self.lock_path = self.config_path.with_suffix(self.config_path.suffix + ".lock")

    def add_user(self, request: AddUserRequest) -> UserResponse:
        with self._locked():
            config = self._read_config()
            inbound = self._get_inbound(config)
            clients = self._get_clients(inbound)

            existing = self._find_client(clients, request.uuid)
            if existing:
                if self._is_reserved(existing):
                    raise ReservedUserError("Reserved user cannot be updated")
                existing.update(self._client_payload(request))
            else:
                if self._count_paying(clients) >= self.settings.xray_max_users:
                    raise UserLimitReached("Xray paying user limit reached")
                clients.append(self._client_payload(request))

            self._write_validate_restart(config)

        return UserResponse(
            uuid=request.uuid,
            email=request.email,
            limit=request.limit,
            flow=request.flow,
            reserved=False,
            connection_uri=self.build_connection_uri(request.uuid, request.email),
        )

    def remove_user(self, uuid: str) -> UserResponse:
        with self._locked():
            config = self._read_config()
            inbound = self._get_inbound(config)
            clients = self._get_clients(inbound)
            existing = self._find_client(clients, uuid)
            if not existing:
                raise UserNotFound("Xray user not found")
            if self._is_reserved(existing):
                raise ReservedUserError("Reserved user cannot be removed")

            clients.remove(existing)
            self._write_validate_restart(config)

        return self._to_response(existing)

    def list_users(self) -> list[UserResponse]:
        config = self._read_config()
        clients = self._get_clients(self._get_inbound(config))
        return [self._to_response(client) for client in clients]

    def count_users(self) -> CountResponse:
        users = self.list_users()
        reserved = sum(1 for user in users if user.reserved)
        total = len(users)
        return CountResponse(
            total=total,
            paying=total - reserved,
            reserved=reserved,
            max_users=self.settings.xray_max_users,
        )

    def test_config(self) -> None:
        if not self.settings.xray_test_cmd:
            return
        command = self.settings.xray_test_cmd.format(config_path=str(self.config_path))
        self._run_command(command)

    def build_connection_uri(self, uuid: str, label: str) -> str:
        public_key = self.settings.reality_public_key or ""
        if not public_key:
            raise ConfigError("REALITY_PUBLIC_KEY must be set to build VLESS connection URI")
        return build_vless_reality_uri(
            uuid,
            self.settings.xray_public_host,
            label,
            public_key=public_key,
            short_id=self.settings.reality_short_id,
            sni=self.settings.reality_sni,
            flow=self.settings.vless_flow,
        )

    def _client_payload(self, request: AddUserRequest) -> dict[str, Any]:
        return {
            "id": request.uuid,
            "flow": request.flow,
            "email": request.email,
            "limit": request.limit,
        }

    def _read_config(self) -> dict[str, Any]:
        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError as exc:
            raise ConfigError(f"Xray config not found: {self.config_path}") from exc
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid Xray config JSON: {exc}") from exc

    def _get_inbound(self, config: dict[str, Any]) -> dict[str, Any]:
        inbounds = config.get("inbounds")
        if not isinstance(inbounds, list):
            raise ConfigError("Xray config must contain an inbounds list")

        for inbound in inbounds:
            if inbound.get("tag") == self.settings.xray_inbound_tag:
                return inbound

        for inbound in inbounds:
            if inbound.get("protocol") == "vless":
                return inbound

        raise ConfigError(f"Xray inbound not found: {self.settings.xray_inbound_tag}")

    def _get_clients(self, inbound: dict[str, Any]) -> list[dict[str, Any]]:
        settings = inbound.setdefault("settings", {})
        clients = settings.setdefault("clients", [])
        if not isinstance(clients, list):
            raise ConfigError("Inbound settings.clients must be a list")
        return clients

    def _find_client(self, clients: list[dict[str, Any]], uuid: str) -> dict[str, Any] | None:
        return next((client for client in clients if client.get("id") == uuid), None)

    def _count_paying(self, clients: list[dict[str, Any]]) -> int:
        return sum(1 for client in clients if not self._is_reserved(client))

    def _is_reserved(self, client: dict[str, Any]) -> bool:
        return (
            client.get("email") in self.settings.reserved_emails()
            or client.get("id") in self.settings.reserved_uuids()
        )

    def _to_response(self, client: dict[str, Any]) -> UserResponse:
        uuid = str(client.get("id", ""))
        email = client.get("email")
        return UserResponse(
            uuid=uuid,
            email=email,
            limit=client.get("limit"),
            flow=client.get("flow"),
            reserved=self._is_reserved(client),
            connection_uri=self.build_connection_uri(uuid, email or uuid) if uuid else None,
        )

    def _write_validate_restart(self, config: dict[str, Any]) -> None:
        original = self._read_config()
        self._atomic_write(config)
        try:
            self.test_config()
            if self.settings.xray_reload_cmd:
                self._run_command(self.settings.xray_reload_cmd)
        except Exception:
            self._atomic_write(original)
            raise

    def _atomic_write(self, config: dict[str, Any]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.config_path.parent,
            delete=False,
        ) as temp:
            json.dump(config, temp, ensure_ascii=False, indent=2)
            temp.write("\n")
            temp_path = Path(temp.name)
        os.replace(temp_path, self.config_path)

    def _run_command(self, command: str) -> None:
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

    @contextmanager
    def _locked(self):
        start = time.monotonic()
        while True:
            try:
                lock_fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                if time.monotonic() - start > self.settings.lock_timeout_seconds:
                    raise ConfigError(f"Could not acquire config lock: {self.lock_path}")
                time.sleep(0.1)

        try:
            os.write(lock_fd, str(os.getpid()).encode("ascii"))
            yield
        finally:
            os.close(lock_fd)
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass
