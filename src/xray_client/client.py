from dataclasses import dataclass
from typing import Any

import httpx


class XrayAgentClientError(Exception):
    """Raised when the Xray Agent request fails."""


@dataclass(slots=True)
class XrayAgentClient:
    base_url: str
    api_key: str
    verify_ssl: bool = False
    timeout_seconds: float = 20.0

    def add_user(self, email: str, uuid: str, limit: int) -> dict[str, Any]:
        return self._request(
            "POST",
            "/add_user",
            json={
                "email": email,
                "uuid": uuid,
                "limit": limit,
                "flow": "xtls-rprx-vision",
            },
        )

    def remove_user(self, uuid: str) -> dict[str, Any]:
        return self._request("POST", "/remove_user", json={"uuid": uuid})

    def users_count(self) -> dict[str, Any]:
        return self._request("GET", "/users/count")

    def users_online_stats(self) -> list[dict[str, Any]]:
        data = self._request("GET", "/stats/users_online")
        if isinstance(data, list):
            return data
        return []

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        try:
            with httpx.Client(
                base_url=self.base_url,
                headers={"X-API-Key": self.api_key},
                verify=self.verify_ssl,
                timeout=self.timeout_seconds,
            ) as client:
                response = client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            raise XrayAgentClientError(
                f"Agent request failed: {exc.response.status_code} {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise XrayAgentClientError(f"Agent request failed: {exc}") from exc
