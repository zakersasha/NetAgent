# Деплой сайта (лендинг + ЛК + админка)

Сервер: **37.230.114.25** (Россия, вместе с bot / postgres / monitor).

Без домена: сайт на `http://37.230.114.25:8001`.

---

## Что поднимается

| URL | Назначение |
|-----|------------|
| `/` | Лендинг, тарифы |
| `/register`, `/login` | Регистрация / вход пользователя |
| `/cabinet` | Личный кабинет, ключ, mock-оплата |
| `/admin/login` | Вход администратора |
| `/admin` | Дашборд, пользователи, платежи, тарифы, тикеты поддержки |

Сервис **web** в `docker-compose.yml` — тот же образ, что bot, команда `python -m webapp.main`.

---

## 1. Переменные `.env`

```env
WEB_SECRET_KEY=<длинная случайная строка>
WEB_PORT=8001

# те же, что для бота:
DATABASE_URL=postgresql+psycopg://...
XRAY_AGENT_URL=...
REALITY_PUBLIC_KEY=...
XRAY_PUBLIC_HOST=51.250.112.128
XRAY_PUBLIC_PORT=2053

# админ (seed при первом запуске)
ADMIN_SEED_EMAIL=adkharlamov.dev@gmail.com
ADMIN_SEED_PASSWORD=<пароль>
```

`WEB_SECRET_KEY` — для cookie-сессий. Сгенерировать:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 2. Запуск

На сервере в каталоге проекта:

```bash
git pull
docker compose up -d --build
docker compose ps
docker compose logs -f web
```

Проверка:

```bash
curl -s http://127.0.0.1:8001/health
```

С вашего ПК: `http://37.230.114.25:8001`

---

## 3. Firewall

Откройте порт **8001** (или тот, что в `WEB_PORT`):

```bash
# ufw пример
sudo ufw allow 8001/tcp
```

---

## 4. Первый вход

**Пользователь:** `/register` → email + пароль → `/cabinet` → тариф → «Оплатить (mock)».

**Админ:** `/admin/login` — email и пароль из `ADMIN_SEED_EMAIL` / `ADMIN_SEED_PASSWORD`.

---

## 5. Связь с Telegram-ботом

- Web и bot используют **одну БД** (`users`, `subscriptions`, `payments`).
- Web-пользователь: `email` + `password_hash`, без `telegram_id`.
- Bot-пользователь: `telegram_id`. Аккаунты пока **не связаны** (можно добавить позже).
- AI-чат — в Telegram-боте; на сайте показывается статус подписки AI.

---

## 6. Локальная разработка

```bash
pip install -e ".[dev]"
# PostgreSQL или DATABASE_URL из .env
python -m webapp.main
```

Открыть `http://127.0.0.1:8001`.

---

## 7. HTTPS и домен (позже)

Когда появится домен — nginx/Caddy перед `web:8001`, Let's Encrypt, `Secure` cookie. Пока MVP на IP + HTTP.

---

## Структура кода

```
src/webapp/
  main.py          — uvicorn
  app.py           — FastAPI factory
  routes/          — landing, auth, cabinet, admin
  templates/       — Jinja2 HTML
  static/css/      — стили
  stats.py         — статистика для админки
  users.py         — регистрация
```

Биллинг переиспользует `BillingClient` из бота (`activate_mock_payment_for_user`, ключи, трафик).
