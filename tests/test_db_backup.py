from db_backup.service import backup_filename, select_files_for_deletion


def test_select_files_for_deletion_keeps_ten_newest() -> None:
    names = [f"netagent-2026-06-{day:02d}_220000.sql.gz" for day in range(1, 16)]
    to_delete = select_files_for_deletion(names, retention_count=10)
    assert len(to_delete) == 5
    assert "netagent-2026-06-01_220000.sql.gz" in to_delete
    assert "netagent-2026-06-15_220000.sql.gz" not in to_delete


def test_select_files_for_deletion_ignores_other_files() -> None:
    names = [
        "netagent-2026-06-10_220000.sql.gz",
        "readme.txt",
        "netagent-old.dump",
    ]
    assert select_files_for_deletion(names, retention_count=10) == []


def test_backup_filename_format() -> None:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    name = backup_filename(datetime(2026, 6, 18, 22, 0, tzinfo=ZoneInfo("Europe/Moscow")))
    assert name == "netagent-2026-06-18_220000.sql.gz"
