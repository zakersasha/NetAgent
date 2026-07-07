# Бэкап PostgreSQL на Яндекс.Диск

Ежедневный дамп БД вечером (по умолчанию **22:00 MSK**), загрузка на Яндекс.Диск, хранение **10 последних** копий.

Сервис: `db-backup` в `docker-compose.yml`.

---

## 1. Приложение в Яндексе

1. [oauth.yandex.ru](https://oauth.yandex.ru/) → **Создать приложение**.
2. Платформы: **Веб-сервисы** (или подходящая для server-side).
3. Права: **Яндекс.Диск REST API** → запись (`cloud_api:disk.write`).
4. Скопируйте **ClientID** и **Client secret**.

---

## 2. Refresh token (один раз)

На сервере или локально с заполненным `.env`:

```bash
# ClientID и Client secret уже в .env
python -m db_backup.oauth_setup
```

Откройте ссылку → разрешите доступ → вставьте код → скопируйте `YANDEX_DISK_REFRESH_TOKEN` в `.env`.

---

## 3. `.env`

```env
BACKUP_ENABLED=true
BACKUP_HOUR=22
BACKUP_MINUTE=0
BACKUP_RETENTION_COUNT=10

YANDEX_DISK_CLIENT_ID=ваш_client_id
YANDEX_DISK_CLIENT_SECRET=ваш_client_secret
YANDEX_DISK_REFRESH_TOKEN=полученный_refresh_token
YANDEX_DISK_BACKUP_PATH=/NetAgent/backups

POSTGRES_USER=netagent
POSTGRES_PASSWORD=...
POSTGRES_DB=netagent
```

---

## 4. Запуск

```bash
docker compose up -d --build db-backup
docker compose logs -f db-backup
```

В логах: `Next backup in ...` и после 22:00 — `Backup completed: netagent-YYYY-MM-DD_HHMMSS.sql.gz`.

---

## 5. Ручной бэкап (тест)

```bash
docker compose run --rm db-backup python -c "
from db_backup.service import DatabaseBackupService
from db_backup.settings import get_backup_settings
print(DatabaseBackupService(get_backup_settings()).run_once())
"
```

---

## 6. Восстановление

```bash
# скачайте .sql.gz с Яндекс.Диска на сервер
gunzip -c netagent-2026-06-18_220000.sql.gz > restore.sql

docker compose exec -T postgres psql -U netagent -d netagent < restore.sql
```

Для чистой БД сначала пересоздайте базу (осторожно, удалит данные):

```bash
docker compose exec postgres psql -U netagent -d postgres -c "DROP DATABASE netagent;"
docker compose exec postgres psql -U netagent -d postgres -c "CREATE DATABASE netagent;"
```

---

## 7. Формат файлов

| Имя | Пример |
|-----|--------|
| Папка на Диске | `/NetAgent/backups` |
| Файл | `netagent-2026-06-18_220000.sql.gz` |

Старые файлы сверх лимита **10** удаляются автоматически после каждой успешной загрузки.

---

## 8. Отключить

```env
BACKUP_ENABLED=false
```

```bash
docker compose up -d db-backup
```

Сервис останется запущенным, но бэкапы не выполняются.
