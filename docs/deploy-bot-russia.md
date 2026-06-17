# Telegram-бот — запуск через Docker

Сервер: **37.230.114.25** (Россия)

## 1. Токен

Создайте бота в [@BotFather](https://t.me/BotFather) → `/newbot` → скопируйте токен.

## 2. Запуск

```bash
cd /opt/netagent

cp .env.example .env
nano .env   # TELEGRAM_BOT_TOKEN, POSTGRES_PASSWORD, REALITY_PUBLIC_KEY, XRAY_AGENT_API_KEY

docker compose up -d --build
```

## 3. Логи и остановка

```bash
docker compose logs -f bot
docker compose down
```

## 4. Проверка

В Telegram: `/start` → **Купить подписку** → тариф → **Оплатить (тест)**.

Проверка токена с сервера:

```bash
source .env
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
```

## 5. Прокси (сервер в РФ)

Telegram API из России часто недоступен. В `.env`:

```env
BOT_PROXY_URL=http://user:pass@45.93.137.80:3128
```

Проверка с сервера:

```bash
source .env
curl -x "$BOT_PROXY_URL" -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
```

## 6. PostgreSQL

- Единая БД для бота и будущей админки — данные сохраняются между перезапусками.
- Подключение с ПК: [docs/deploy-database.md](deploy-database.md).
- В `.env`: `POSTGRES_PASSWORD`, `DATABASE_URL`, при необходимости `ADMIN_SEED_PASSWORD`.

## 7. Сейчас (mock)

- Оплата тестовая, без ЮKassa.
- При оплате активируется подписка; устройство добавляется отдельно через «Мои устройства».
- При добавлении устройства бот вызывает Xray Agent на Литве.
- `XRAY_AGENT_TIMEOUT_SECONDS=60` — timeout на запись config + restart Xray.

## 8. Если бот падает

| Ошибка | Решение |
|--------|---------|
| `TELEGRAM_BOT_TOKEN в .env` | Заполнить `.env`, не оставлять пустой и не `mock-token` |
| `Request timeout` | Задать `BOT_PROXY_URL` в `.env` |
| `Agent request failed: timed out` | Проверить доступ к `XRAY_AGENT_URL`, логи `netagent-xray-agent`, увеличить `XRAY_AGENT_TIMEOUT_SECONDS` |
| `Unauthorized` | Неверный токен |
| Бот не отвечает | `docker compose logs -f bot` |
