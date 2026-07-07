import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

YANDEX_OAUTH_URL = "https://oauth.yandex.ru/token"
YANDEX_DISK_API = "https://cloud-api.yandex.net/v1/disk"


class YandexDiskError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DiskResource:
    name: str
    path: str


class YandexDiskClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        *,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._client_id = client_id.strip()
        self._client_secret = client_secret.strip()
        self._refresh_token = refresh_token.strip()
        self._timeout = timeout_seconds
        self._access_token: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self._client_id and self._client_secret and self._refresh_token)

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        token = self._ensure_access_token()
        upload_href = self._request_upload_href(token, remote_path)
        with local_path.open("rb") as handle:
            response = httpx.put(
                upload_href,
                content=handle.read(),
                timeout=self._timeout,
            )
        if response.status_code not in (201, 202):
            raise YandexDiskError(
                f"Upload failed HTTP {response.status_code}: {response.text[:300]}"
            )

    def list_files(self, folder_path: str) -> list[DiskResource]:
        token = self._ensure_access_token()
        encoded = quote(folder_path, safe="/")
        url = f"{YANDEX_DISK_API}/resources?path={encoded}&limit=1000"
        response = httpx.get(
            url,
            headers={"Authorization": f"OAuth {token}"},
            timeout=self._timeout,
        )
        if response.status_code == 404:
            return []
        if response.status_code >= 400:
            raise YandexDiskError(
                f"List failed HTTP {response.status_code}: {response.text[:300]}"
            )
        payload = response.json()
        embedded = payload.get("_embedded") or {}
        items = embedded.get("items") or []
        result: list[DiskResource] = []
        for item in items:
            if item.get("type") != "file":
                continue
            name = str(item.get("name", "")).strip()
            path = str(item.get("path", "")).strip()
            if name and path:
                result.append(DiskResource(name=name, path=path))
        return result

    def delete(self, remote_path: str) -> None:
        token = self._ensure_access_token()
        encoded = quote(remote_path, safe="/")
        url = f"{YANDEX_DISK_API}/resources?path={encoded}&permanently=true"
        response = httpx.delete(
            url,
            headers={"Authorization": f"OAuth {token}"},
            timeout=self._timeout,
        )
        if response.status_code in (202, 204, 404):
            return
        raise YandexDiskError(
            f"Delete failed HTTP {response.status_code}: {response.text[:300]}"
        )

    def ensure_folder(self, folder_path: str) -> None:
        token = self._ensure_access_token()
        encoded = quote(folder_path, safe="/")
        url = f"{YANDEX_DISK_API}/resources?path={encoded}"
        response = httpx.put(
            url,
            headers={"Authorization": f"OAuth {token}"},
            timeout=self._timeout,
        )
        if response.status_code in (201, 409):
            return
        if response.status_code >= 400:
            raise YandexDiskError(
                f"Create folder failed HTTP {response.status_code}: {response.text[:300]}"
            )

    def _request_upload_href(self, token: str, remote_path: str) -> str:
        encoded = quote(remote_path, safe="/")
        url = (
            f"{YANDEX_DISK_API}/resources/upload"
            f"?path={encoded}&overwrite=true"
        )
        response = httpx.get(
            url,
            headers={"Authorization": f"OAuth {token}"},
            timeout=self._timeout,
        )
        if response.status_code >= 400:
            raise YandexDiskError(
                f"Upload href failed HTTP {response.status_code}: {response.text[:300]}"
            )
        href = response.json().get("href")
        if not href:
            raise YandexDiskError("Yandex Disk did not return upload href")
        return href

    def _ensure_access_token(self) -> str:
        if self._access_token:
            return self._access_token
        response = httpx.post(
            YANDEX_OAUTH_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
            timeout=self._timeout,
        )
        if response.status_code >= 400:
            raise YandexDiskError(
                f"OAuth refresh failed HTTP {response.status_code}: {response.text[:300]}"
            )
        token = response.json().get("access_token")
        if not token:
            raise YandexDiskError("OAuth response missing access_token")
        self._access_token = token
        return token
