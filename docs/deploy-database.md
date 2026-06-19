# PostgreSQL — единая база (бот + админка)

Сервер: **37.230.114.25** (Россия)

## Запуск

```bash
cp .env.example .env
# POSTGRES_PASSWORD, TELEGRAM_BOT_TOKEN, ...

docker compose up -d --build
docker compose logs -f bot
docker compose logs -f postgres
```

При старте бот автоматически:
1. `alembic upgrade head` — создаёт таблицы
2. seed тарифов и admin (если задан `ADMIN_SEED_PASSWORD`)
3. запускает polling

## Подключение с вашего компьютера

### Вариант A — открытый порт (динамический IP)

Если домашний IP меняется, whitelist по IP неудобен. Можно открыть Postgres наружу и полагаться на **длинный пароль** (20+ символов, буквы + цифры + спецсимволы).

**1. На сервере:**

```bash
# пароль только в .env, не в командной строке
sudo ufw allow 5432/tcp
sudo ufw status
```

Docker уже пробрасывает порт из `docker-compose.yml` (`POSTGRES_PORT` → 5432 в контейнере).

**2. В `.env`:**

```env
POSTGRES_PASSWORD=...   # длинный, уникальный
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://netagent:ПАРОЛЬ@postgres:5432/netagent
```

После смены пароля: `docker compose up -d` (пересоздаёт postgres только при первом запуске; для смены пароля в уже созданной БД — `ALTER USER` в psql).

**3. С ПК (DBeaver, DataGrip, psql):**

| Поле | Значение |
|------|----------|
| Host | `37.230.114.25` |
| Port | `5432` (или `POSTGRES_PORT` из `.env`) |
| Database | `netagent` |
| User | `netagent` |
| Password | `POSTGRES_PASSWORD` |

```
postgresql://netagent:PASSWORD@37.230.114.25:5432/netagent
```

```bash
psql "postgresql://netagent:PASSWORD@37.230.114.25:5432/netagent"
```

**Снизить шум сканеров:** в `.env` можно поставить нестандартный внешний порт, например `POSTGRES_PORT=15432`, и в DBeaver указать порт `15432`. На сервере: `sudo ufw allow 15432/tcp` (и убрать 5432, если открывали).

### Вариант B — SSH-туннель (без открытия 5432)

Порт наружу не нужен; работает с любым IP.

```bash
ssh -N -L 15432:127.0.0.1:5432 root@37.230.114.25
```

В DBeaver: host `127.0.0.1`, port `15432`, остальное как выше.

## Таблицы MVP

- `users` — клиенты (telegram_id)
- `plans` — тарифы
- `subscriptions` — подписки
- `devices` — отдельный UUID на устройство
- `payments` — оплаты
- `admin_users` — админка

## Ручные команды

```bash
# миграции
docker compose run --rm bot alembic upgrade head

# только seed
docker compose run --rm bot python -c "
from netagent_db.seed import run_seed
from netagent_db.session import create_session_factory
import os
sf = create_session_factory(os.environ['DATABASE_URL'])
with sf() as s: run_seed(s)
"
```

## Безопасность

| Открытый 5432 + сильный пароль | Плюсы: просто с любого IP. Минусы: боты постоянно стучат в порт; при утечке пароля из `.env` / DBeaver — полный доступ. |
| SSH-туннель | Плюсы: Postgres не виден с интернета. Минусы: нужен SSH при каждом подключении (или autossh). |

Рекомендации при открытом порте:
- пароль **не короче 20 символов**, не из словаря;
- не коммитить `.env`, не сохранять пароль в скриншоты;
- в DBeaver отключить «сохранять пароль» на общем ПК, если это важно;
- периодически смотреть `docker compose logs postgres` на failed auth;
- при возможности — нестандартный `POSTGRES_PORT` вместо 5432.
