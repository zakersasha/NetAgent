# Брендинг Telegram-бота (BotFather)

Акцент: **AI-ассистент** в Telegram. Подключение — дополнительная опция в тарифах, без акцента на VPN в публичных текстах.

Описание и short description задаются автоматически при запуске бота (`setMyDescription`). Ниже — тексты для ручной настройки в BotFather, если нужно.

## Описание бота (Description, до 512 символов)

```
AI-ассистент в Telegram: задайте вопрос и получите ответ.
3 сообщения бесплатно каждый день.
Тарифы: безлимитный чат, Combo — AI + стабильное подключение.
Поддержка: /support
```

## Короткое описание (Short description)

```
AI-ассистент и подписки. Чат, тарифы, поддержка.
```

## Текст кнопки Start / приветствие

```
Ваш умный помощник: чат с AI, ответы на вопросы и идеи на каждый день.
3 сообщения бесплатно. Тарифы — безлимитный чат и Combo с подключением.
```

## Промпт для картинки бота (аватар 512×512)

```
Minimal modern app icon for a Telegram AI assistant bot.
Friendly chat bubble with subtle sparkles, soft blue and purple gradient,
clean geometric shapes, trustworthy and approachable mood.
No text, no VPN word, no flags, no prohibited symbols.
Flat vector style, suitable for small circular avatar.
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/chat` | Чат с ассистентом |
| `/plans` | Тарифы |
| `/devices` | Мои ключи |
| `/help` | Как подключить |
| `/support` | Поддержка |
| `/stop` | Выйти из чата |

Команды и описание регистрируются автоматически при запуске бота.

## Настройки в `.env`

```env
BOT_SERVICE_NAME=NetAgent
BOT_SUPPORT_CONTACT=@sashakharlamov
SUPPORT_NOTIFY_TELEGRAM_ID=123456789
```

`SUPPORT_NOTIFY_TELEGRAM_ID` — ваш числовой Telegram ID для оповещений о тикетах поддержки.
