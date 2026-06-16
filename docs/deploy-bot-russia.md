# Telegram-бот — запуск через Docker

Сервер: **37.230.114.25** (Россия)

## 1. Токен

Создайте бота в [@BotFather](https://t.me/BotFather) → `/newbot` → скопируйте токен.

## 2. Запуск

```bash
cd /opt/netagent

cp .env.example .env
nano .env   # вставить TELEGRAM_BOT_TOKEN=...

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

## 5. Сейчас (mock)

- Оплата тестовая, без ЮKassa.
- Подписки в памяти — после `docker compose down` сбрасываются.
- Ключ в боте **mock** — в Xray на Литве client ещё не создаётся.

## 6. Если бот падает

| Ошибка | Решение |
|--------|---------|
| `TELEGRAM_BOT_TOKEN в .env` | Заполнить `.env`, не оставлять пустой и не `mock-token` |
| `Unauthorized` | Неверный токен |
| Бот не отвечает | `docker compose logs -f bot` |
