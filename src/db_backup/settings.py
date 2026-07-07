from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackupSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    enabled: bool = Field(True, alias="BACKUP_ENABLED")
    timezone: str = Field("Europe/Moscow", alias="TIMEZONE")
    backup_hour: int = Field(22, alias="BACKUP_HOUR")
    backup_minute: int = Field(0, alias="BACKUP_MINUTE")
    retention_count: int = Field(10, alias="BACKUP_RETENTION_COUNT")

    postgres_host: str = Field("postgres", alias="BACKUP_POSTGRES_HOST")
    postgres_port: int = Field(5432, alias="BACKUP_POSTGRES_PORT")
    postgres_user: str = Field("netagent", alias="POSTGRES_USER")
    postgres_password: str = Field("", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field("netagent", alias="POSTGRES_DB")

    yandex_client_id: str = Field("", alias="YANDEX_DISK_CLIENT_ID")
    yandex_client_secret: str = Field("", alias="YANDEX_DISK_CLIENT_SECRET")
    yandex_refresh_token: str = Field("", alias="YANDEX_DISK_REFRESH_TOKEN")
    yandex_backup_path: str = Field("/NetAgent/backups", alias="YANDEX_DISK_BACKUP_PATH")


@lru_cache
def get_backup_settings() -> BackupSettings:
    return BackupSettings()
