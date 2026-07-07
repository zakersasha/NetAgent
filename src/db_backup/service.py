import gzip
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from db_backup.settings import BackupSettings
from db_backup.yandex_disk import YandexDiskClient, YandexDiskError

logger = logging.getLogger(__name__)

BACKUP_PREFIX = "netagent-"


def backup_filename(now: datetime) -> str:
    return f"{BACKUP_PREFIX}{now.strftime('%Y-%m-%d_%H%M%S')}.sql.gz"


def select_files_for_deletion(filenames: list[str], retention_count: int) -> list[str]:
    """Keep newest `retention_count` backup files by name (date in filename)."""
    backup_names = sorted(
        (name for name in filenames if name.startswith(BACKUP_PREFIX) and name.endswith(".sql.gz")),
        reverse=True,
    )
    if len(backup_names) <= retention_count:
        return []
    return backup_names[retention_count:]


class DatabaseBackupService:
    def __init__(self, settings: BackupSettings) -> None:
        self._settings = settings
        self._disk = YandexDiskClient(
            settings.yandex_client_id,
            settings.yandex_client_secret,
            settings.yandex_refresh_token,
        )

    def run_once(self) -> str:
        if not self._settings.enabled:
            raise RuntimeError("BACKUP_ENABLED=false")
        if not self._settings.postgres_password:
            raise RuntimeError("POSTGRES_PASSWORD is not set")
        if not self._disk.configured:
            raise RuntimeError(
                "Задайте YANDEX_DISK_CLIENT_ID, YANDEX_DISK_CLIENT_SECRET и YANDEX_DISK_REFRESH_TOKEN"
            )

        tz = ZoneInfo(self._settings.timezone)
        now = datetime.now(tz)
        filename = backup_filename(now)
        remote_path = f"{self._settings.yandex_backup_path.rstrip('/')}/{filename}"

        with tempfile.TemporaryDirectory(prefix="netagent-backup-") as tmp:
            local_plain = Path(tmp) / "dump.sql"
            local_gz = Path(tmp) / filename
            self._create_dump(local_plain)
            self._gzip_file(local_plain, local_gz)

            self._disk.ensure_folder(self._settings.yandex_backup_path.rstrip("/"))
            logger.info("Uploading backup to Yandex Disk: %s", remote_path)
            self._disk.upload_file(local_gz, remote_path)

            self._rotate_old_backups()

        logger.info("Backup completed: %s", filename)
        return filename

    def _create_dump(self, output_path: Path) -> None:
        env = os.environ.copy()
        env["PGPASSWORD"] = self._settings.postgres_password
        command = [
            "pg_dump",
            "-h",
            self._settings.postgres_host,
            "-p",
            str(self._settings.postgres_port),
            "-U",
            self._settings.postgres_user,
            "-d",
            self._settings.postgres_db,
            "--no-owner",
            "--no-privileges",
            "-f",
            str(output_path),
        ]
        logger.info("Running pg_dump to %s", output_path)
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"pg_dump failed ({result.returncode}): {result.stderr.strip() or result.stdout.strip()}"
            )

    @staticmethod
    def _gzip_file(source: Path, target: Path) -> None:
        with source.open("rb") as src, gzip.open(target, "wb", compresslevel=6) as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)

    def _rotate_old_backups(self) -> None:
        folder = self._settings.yandex_backup_path.rstrip("/")
        files = self._disk.list_files(folder)
        to_delete = select_files_for_deletion(
            [item.name for item in files],
            self._settings.retention_count,
        )
        if not to_delete:
            logger.info("Rotation: nothing to delete (retention=%s)", self._settings.retention_count)
            return

        by_name = {item.name: item.path for item in files}
        for name in to_delete:
            remote_path = by_name.get(name)
            if not remote_path:
                continue
            logger.info("Deleting old backup: %s", name)
            try:
                self._disk.delete(remote_path)
            except YandexDiskError as exc:
                logger.error("Failed to delete %s: %s", name, exc)
