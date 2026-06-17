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

**1. На сервере откройте порт только для вашего IP:**

```bash
# ваш домашний IP
curl -4 ifconfig.me

sudo ufw allow from YOUR_HOME_IP to any port 5432 proto tcp
sudo ufw status
```

**2. В `.env` на сервере:**

```env
POSTGRES_PORT=5432
POSTGRES_PASSWORD=your-strong-password
```

**3. С ПК (DBeaver, DataGrip, psql):**

| Поле | Значение |
|------|----------|
| Host | `37.230.114.25` |
| Port | `5432` |
| Database | `netagent` |
| User | `netagent` |
| Password | из `POSTGRES_PASSWORD` |

URL:

```
postgresql://netagent:PASSWORD@37.230.114.25:5432/netagent
```

**psql:**

```bash
psql "postgresql://netagent:PASSWORD@37.230.114.25:5432/netagent"
```

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

- Не открывайте `5432` для всего интернета (`ufw allow 5432` без `from` — плохая идея).
- Используйте длинный `POSTGRES_PASSWORD`.
- Для продакшена можно поднять Postgres только во внутренней сети и подключаться через SSH tunnel.
