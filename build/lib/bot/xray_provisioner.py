import logging
from dataclasses import dataclass

from xray_client.client import XrayAgentClient, XrayAgentClientError

logger = logging.getLogger(__name__)


class XrayProvisionerError(RuntimeError):
    """Xray key could not be provisioned or revoked."""


@dataclass(slots=True)
class XrayProvisioner:
    """Adds/removes VLESS clients in Xray config via xray-agent HTTP API."""

    client: XrayAgentClient | None
    required: bool = False

    def check_available(self) -> None:
        if not self.client:
            if self.required:
                raise XrayProvisionerError(
                    "Xray Agent не настроен. Задайте XRAY_AGENT_URL и XRAY_AGENT_API_KEY в .env."
                )
            return
        try:
            self.client.health()
        except XrayAgentClientError as exc:
            raise XrayProvisionerError(f"Xray Agent недоступен: {exc}") from exc

    def provision_key(self, *, email: str, uuid: str) -> None:
        """Register a new client in Xray (one key = one device slot)."""
        if not self.client:
            if self.required:
                raise XrayProvisionerError(
                    "Xray Agent не настроен. Задайте XRAY_AGENT_URL и XRAY_AGENT_API_KEY в .env."
                )
            logger.warning("Xray Agent не настроен — ключ %s создан только в БД", email)
            return
        try:
            self.client.add_user(email=email, uuid=uuid, limit=1)
        except XrayAgentClientError as exc:
            raise XrayProvisionerError(f"Не удалось добавить ключ в Xray: {exc}") from exc

    def revoke_key(self, *, uuid: str) -> None:
        """Remove client from Xray config."""
        if not self.client:
            return
        try:
            self.client.remove_user(uuid=uuid)
        except XrayAgentClientError as exc:
            raise XrayProvisionerError(f"Не удалось удалить ключ из Xray: {exc}") from exc

    def rollback_key(self, *, uuid: str) -> None:
        """Best-effort cleanup after a failed DB write."""
        if not self.client:
            return
        try:
            self.client.remove_user(uuid=uuid)
        except XrayAgentClientError:
            logger.exception("Rollback remove_user failed for uuid=%s", uuid)
