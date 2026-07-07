"""One-time OAuth helper: obtain YANDEX_DISK_REFRESH_TOKEN.

Usage:
  python -m db_backup.oauth_setup

Requires YANDEX_DISK_CLIENT_ID and YANDEX_DISK_CLIENT_SECRET in .env
"""

import sys

import httpx

from db_backup.settings import get_backup_settings

AUTH_URL = "https://oauth.yandex.ru/authorize"
TOKEN_URL = "https://oauth.yandex.ru/token"
SCOPE = "cloud_api:disk.write"


def main() -> None:
    settings = get_backup_settings()
    if not settings.yandex_client_id or not settings.yandex_client_secret:
        print("Задайте YANDEX_DISK_CLIENT_ID и YANDEX_DISK_CLIENT_SECRET в .env")
        sys.exit(1)

    auth_link = (
        f"{AUTH_URL}?response_type=code"
        f"&client_id={settings.yandex_client_id}"
        f"&scope={SCOPE}"
    )
    print("1. Откройте ссылку в браузере и разрешите доступ к Яндекс.Диску:")
    print(auth_link)
    print()
    code = input("2. Вставьте код подтверждения: ").strip()
    if not code:
        print("Код не введён")
        sys.exit(1)

    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.yandex_client_id,
            "client_secret": settings.yandex_client_secret,
        },
        timeout=30.0,
    )
    if response.status_code >= 400:
        print(f"Ошибка OAuth: HTTP {response.status_code}\n{response.text}")
        sys.exit(1)

    payload = response.json()
    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        print(f"Нет refresh_token в ответе: {payload}")
        sys.exit(1)

    print()
    print("Добавьте в .env:")
    print(f"YANDEX_DISK_REFRESH_TOKEN={refresh_token}")


if __name__ == "__main__":
    main()
