# Брендинг Telegram-бота (BotFather)

Без слова «VPN» в публичных текстах. Акцент: личный канал, стабильный доступ, простое подключение.

## Описание бота (Description, до 512 символов)

```
Личный канал для стабильного доступа к сайтам и приложениям.
Тарифы на 30 дней, ключ в боте, инструкции для телефона и ПК.
Поддержка: @sashakharlamov
```

## Короткое описание (Short description)

```
Ключ подключения за пару минут. Тарифы, инструкции, поддержка.
```

## Текст кнопки Start / приветствие (About или welcome в BotFather)

```
Добро пожаловать! Здесь вы получите персональный ключ для стабильного доступа.
Выберите тариф, скопируйте ключ и подключите в приложении — шаги в «Инструкции».
```

## Промпт для картинки бота (аватар 512×512)

```
Minimal modern app icon for a Telegram bot about personal secure internet access.
Abstract glowing key or link symbol in the center, soft blue and teal gradient background,
clean geometric shapes, subtle network lines, friendly and trustworthy mood.
No text, no VPN word, no flags, no prohibited symbols.
Flat vector style, rounded corners feel, high contrast, suitable for small circular avatar.
Professional SaaS aesthetic, light and airy, not dark hacker style.
```

Альтернатива (более «продающий» вариант):

```
Friendly Telegram bot avatar: abstract shield made of connected dots and a small keyhole,
gradient from sky blue to mint green, white highlights, minimal flat design,
positive and simple, no words, no VPN labels, 512x512 app icon style.
```

## Команды бота (опционально)

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/plans` | Тарифы |
| `/devices` | Мои устройства |
| `/help` | Инструкции |
| `/support` | Поддержка |

Команды регистрируются автоматически при запуске бота (`setMyCommands`).

## Настройки в `.env`

```env
BOT_SERVICE_NAME=NetAgent
BOT_SUPPORT_CONTACT=@sashakharlamov
```

Кнопка «Поддержка» в боте ведёт на https://t.me/sashakharlamov
