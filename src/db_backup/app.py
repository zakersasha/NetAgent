import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from db_backup.service import DatabaseBackupService
from db_backup.settings import get_backup_settings

logger = logging.getLogger(__name__)


def _seconds_until_next_run(now: datetime, hour: int, minute: int) -> float:
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return max(1.0, (target - now).total_seconds())


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_backup_settings()

    if not settings.enabled:
        logger.warning("BACKUP_ENABLED=false — db-backup service idle")
        while True:
            await asyncio.sleep(3600)

    service = DatabaseBackupService(settings)
    tz = ZoneInfo(settings.timezone)
    logger.info(
        "DB backup scheduler: daily at %02d:%02d %s, retention=%s copies, folder=%s",
        settings.backup_hour,
        settings.backup_minute,
        settings.timezone,
        settings.retention_count,
        settings.yandex_backup_path,
    )

    while True:
        now = datetime.now(tz)
        delay = _seconds_until_next_run(now, settings.backup_hour, settings.backup_minute)
        logger.info("Next backup in %.0f seconds (~%s)", delay, (now + timedelta(seconds=delay)).isoformat())
        await asyncio.sleep(delay)
        try:
            await asyncio.to_thread(service.run_once)
        except Exception:
            logger.exception("Scheduled backup failed")


if __name__ == "__main__":
    asyncio.run(main())
