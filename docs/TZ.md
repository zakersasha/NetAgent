# Техническое задание (ТЗ)
# NetAgent — MVP платформа продажи VPN-подписок (Xray)

**Версия:** 1.6  
**Дата:** 15.06.2026  
**Статус:** Утверждение  
**Changelog 1.6:** Без алертов; один admin; без backup PostgreSQL; админка — источник информации о сервисе.  
**Changelog 1.5:** Продление `now+30` MSK; тот же UUID; апгрейд/даунгрейд; без trial; admin client reserved; seed admin email; бот/бренд — последний этап.  
**Changelog 1.4:** Mock-оплата; `limit` в Xray; Agent 8443; `/add_user` `/remove_user`.  
**Changelog 1.3:** IP российского сервера `37.230.114.25`; раздел вопросов для финализации ТЗ.  
**Changelog 1.2:** Двухсерверный деплой (Литва / Россия); тарифы Start/Standard/Family с ценами; IP 45.93.137.80; `systemctl restart xray`.  
**Changelog 1.1:** ЮKassa; тарифы 1–3 устройств; конфиг VLESS+Reality; управление ключами через микросервис правки конфига.

---

## 1. Общее описание

### 1.1 Цель проекта

Создать MVP-систему для продажи и управления подписками на VPN-сервер на базе **Xray-core** (уже развёрнут, локация: **Литва**). Система должна автоматизировать выдачу ключей, контроль срока подписки, ограничение числа устройств и предоставлять каналы продаж через Telegram и веб-сайт.

### 1.2 Ключевые ограничения MVP

| Параметр | Значение |
|----------|----------|
| Максимум активных ключей на VPN-сервере | **50** |
| Тип подписки (MVP) | **Только месячная** (30 дней) |
| VPN-протокол | **VLESS + Reality** (XTLS-Vision) |
| Тарифы | **3 тарифа** — Start / Standard / Family (1–3 устройств) |
| Оплата (разработка) | **Mock** — имитация оплаты |
| Оплата (production) | **ЮKassa** — **последний этап** (после домена) |
| Лимит устройств | Поле **`limit`** в client Xray config (1/2/3) |
| Мониторинг online / suspension | **Не в MVP** |
| Протоколы | **Только VLESS + Reality**; WireGuard и прокси — **не в scope** |
| Config Xray | **`/usr/local/etc/xray/config.json`** |
| Xray Agent | FastAPI **8443**, self-signed HTTPS, `X-API-Key` |
| Часовой пояс | **MSK** (`Europe/Moscow`) |
| Продление | **Всегда `сегодня + 30 дней`** (не стак) |
| UUID при продлении | **Тот же** (ключ не меняется) |
| Мульти-месяц | **Нельзя** — только 1 месяц за оплату |
| Апгрейд / даунгрейд | **Разрешён** при покупке/продлении |
| Пробный период | **Нет** |
| Admin VPN client | **Оставить** в config; **не в лимите 50** |
| Первый admin | `adkharlamov.dev@gmail.com` (**один** admin) |
| Алерты | **Нет** — информация только в админ-панели |
| Backup PostgreSQL | **Не в MVP** |
| Бот и бренд | **Mock** → финальный этап с доменом/ЮKassa |
| Публичный адрес VPN (ссылки) | **`45.93.137.80`** (Литва, без домена) |
| Reload Xray | **`systemctl restart xray`** |
| Язык разработки | **Python 3.11+** |
| БД | **PostgreSQL 15+** |
| Контейнеризация | **Docker** + Docker Compose |
| Деплой | **2 сервера**: Литва (VPN + Agent), Россия (БД + приложения) |

### 1.3 Принципы разработки

- Поэтапная реализация компонентов (см. раздел 10).
- Один монорепозиторий `NetAgent` с чёткой модульной структурой.
- Общая бизнес-логика и модели данных — в core-пакете; клиенты (бот, API, лендинг) используют их.
- Все секреты — через переменные окружения / `.env` (не в репозитории).
- MVP: минимальный, но расширяемый функционал без over-engineering.
- **Управление ключами Xray** — через собственный микросервис на VPN-сервере, который правит JSON-конфиг и перезагружает Xray (не gRPC HandlerService).

---

## 2. Архитектура системы

### 2.1 Двухсерверная топология

На **литовском сервере** размещаются **только** VPN и API для правки конфига. Вся бизнес-логика, БД, бот и лендинг — на **российском сервере**.

```
┌──────────────────────────────────────────────────────────────────┐
│           Российский сервер · 37.230.114.25                      │
│  ┌─────────┬─────────┬─────────┬─────────┐                       │
│  │   API   │   Bot   │  Admin  │  Web    │  Landing + ЛК         │
│  │ FastAPI │ aiogram │         │         │                       │
│  └────┬────┴────┬────┴────┬────┴────┬────┘                       │
│       │         Core (payment mock → yookassa, xray HTTP client)     │
│       └─────────────────┬────────────────────────────────────────│
│                         ▼                                        │
│                  PostgreSQL                                      │
└─────────────────────────┬────────────────────────────────────────┘
                          │ HTTPS REST (API key + IP whitelist)
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│     Литовский сервер · 45.93.137.80                              │
│  ┌──────────────────┐      ┌─────────────────────────────┐       │
│  │  xray-agent      │─────▶│  xray-core (systemd)         │       │
│  │  FastAPI :8443   │      │  config.json                 │       │
│  │  HTTPS self-sign │      │  VLESS+Reality, порт 443     │       │
│  │  restart xray    │      │  лимит: 50 clients           │       │
│  └──────────────────┘      └─────────────────────────────┘       │
│  ⚠ На этом сервере НЕТ: БД, бота, лендинга, ЮKassa webhook       │
└──────────────────────────────────────────────────────────────────┘
```

| Сервер | Локация | IP (известный) | Компоненты |
|--------|---------|----------------|------------|
| **App** | Россия | **37.230.114.25** | `postgres`, `api`, `bot`, `web`, `admin`, scheduler |
| **VPN** | Литва | **45.93.137.80** | `xray` (systemd), `xray-agent` |

### 2.2 Сервисы Docker Compose — российский сервер

| Сервис | Описание |
|--------|----------|
| `postgres` | PostgreSQL |
| `api` | FastAPI — REST API, mock-оплата (→ ЮKassa на финальном этапе), HTTP-клиент Xray Agent |
| `bot` | Telegram-бот (aiogram 3.x) |
| `admin` | Панель администратора |
| `web` | Лендинг + личный кабинет |
| `redis` | (опционально, этап 2+) кэш, очереди |

**Файл:** `docker/docker-compose.yml` (app).  
**Локальная разработка:** все сервисы на одной машине; Agent — mock или tunnel к Литве.

### 2.3 Деплой на литовском сервере

| Компонент | Способ запуска |
|-----------|----------------|
| `xray` | **systemd** (`systemctl restart xray`) |
| `xray-agent` | systemd unit или Docker (один контейнер) |

**Файл:** `docker/docker-compose.vpn.yml` или `docs/deploy-lithuania.md`.

| Сервис | Описание |
|--------|----------|
| `xray-agent` | FastAPI на **8443** — `/add_user`, `/remove_user`; правка `/usr/local/etc/xray/config.json` + `systemctl restart xray` |

### 2.4 Сетевое взаимодействие

- **Россия → Литва:** биллинг-сервер вызывает `https://45.93.137.80:8443` (self-signed TLS, verify отключён или CA pin).
- **Аутентификация Agent:** заголовок `X-API-Key` (или `Authorization: Bearer <key>`).
- **Пользователи → VPN:** **45.93.137.80:443** (VLESS Reality).
- **Xray Agent:** whitelist IP **`37.230.114.25`**.
- **Лендинг / ЛК:** `http://37.230.114.25` до домена.
- Firewall Литвы: **443** — публично; **8443** — только **37.230.114.25**.
- **ЮKassa webhook и домен** — финальный этап (не блокирует разработку на mock).

---

## 3. Конфигурация Xray (текущий сервер)

### 3.1 Путь и структура config

| Параметр | Значение |
|----------|----------|
| Путь | **`/usr/local/etc/xray/config.json`** |
| Запуск Xray | systemd читает этот файл при старте |
| Reload после правки | **`systemctl restart xray`** |

Базовая структура inbound (client с лимитом устройств):

```json
{
  "log": { "loglevel": "warning" },
  "inbounds": [
    {
      "tag": "vless-reality-in",
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "<uuid>",
            "flow": "xtls-rprx-vision",
            "email": "user_<id>@netagent.local",
            "limit": 2
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "www.wikipedia.org:443",
          "xver": 0,
          "serverNames": ["www.wikipedia.org"],
          "privateKey": "<REALITY_PRIVATE_KEY>",
          "shortIds": ["6ba85179e30d4fc2"]
        }
      }
    }
  ],
  "outbounds": [
    { "protocol": "freedom" }
  ]
}
```

### 3.2 Параметры для генерации connection URI

| Параметр | Значение |
|----------|----------|
| Протокол | `vless` |
| Порт | `443` |
| Flow | `xtls-rprx-vision` |
| Encryption | `none` |
| Security | `reality` |
| Network | `tcp` |
| SNI (`serverNames`) | `www.wikipedia.org` |
| Short ID | `6ba85179e30d4fc2` |
| Reality dest | `www.wikipedia.org:443` |
| Public host | **`45.93.137.80`** (`XRAY_PUBLIC_HOST`) |

**Формат ссылки (пример):**

```
vless://{uuid}@45.93.137.80:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.wikipedia.org&fp=chrome&pbk={reality_public_key}&sid=6ba85179e30d4fc2&type=tcp#{label}
```

- `reality_public_key` — вычисляется из `privateKey` (на стороне Agent или Core при генерации URI).
- `privateKey` хранится **только на VPN-сервере** (env / config), не в репозитории NetAgent.

### 3.3 Лимит устройств через Xray `limit`

При создании пользователя Agent записывает в client поле **`limit`** = выбранному тарифу:

| Тариф | `limit` в config |
|-------|------------------|
| Start | `1` |
| Standard | `2` |
| Family | `3` |

Xray **сам отключает лишние подключения** при превышении `limit`. Дополнительный мониторинг online, Stats API и статус `suspended` **не нужны в MVP**.

При смене тарифа (продление с другим планом) — обновить `limit` в client и перезапустить Xray.

### 3.4 Рекомендации к конфигу

- `tag`: `"vless-reality-in"` — для однозначной идентификации inbound в Agent.
- Поле `email` в каждом client — для reconcile.
- Личный client администратора в config — **оставить**; пометить **reserved** (`AGENT_RESERVED_EMAILS`): не удалять, не в лимите 50.

---

## 4. Модуль 1 — Xray Agent + HTTP Client

**Приоритет:** Этап 1 (первый)  
**Пути:** `src/xray_agent/` (микросервис на VPN), `src/xray_client/` (HTTP-клиент в NetAgent)

### 4.1 Назначение

**Xray Agent** — легковесный микросервис на VPN-сервере. Создание и удаление ключей для MVP выполняется **правкой `config.json`** и перезагрузкой Xray, а не через gRPC `HandlerService`.

**Xray Client** — Python HTTP-клиент в NetAgent, вызывающий Agent API. Используется через `core/services/xray_service.py`.

### 4.2 Почему правка конфига (MVP)

| Плюс | Минусы (post-MVP) |
|------|-------------------|
| Не нужен gRPC API inbound в Xray | Перезагрузка при каждом изменении |
| Полный контроль над `clients[]` | Race conditions при параллельных запросах (решается mutex в Agent) |
| Простая отладка — виден весь конфиг | Позже можно мигрировать на gRPC hot-add |

### 4.3 Xray Agent — HTTP API (FastAPI)

**Стек:** FastAPI на литовском сервере.  
**Порт:** **8443**.  
**TLS:** **self-signed HTTPS** (российский клиент: `verify=False` или pin CA).  
**Аутентификация:** API-ключ в заголовке **`X-API-Key`**.

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/health` | Статус Agent и Xray |
| `GET` | `/users/count` | Количество clients (для лимита 50 и reconcile) |
| `POST` | **`/add_user`** | Добавить client в config |
| `POST` | **`/remove_user`** | Удалить client из config |

**Body `POST /add_user`:**

```json
{
  "uuid": "<uuid>",
  "email": "user_<id>@netagent.local",
  "limit": 2,
  "flow": "xtls-rprx-vision"
}
```

- `limit` — **обязательно**, значение 1 / 2 / 3 по тарифу.

**Body `POST /remove_user`:**

```json
{
  "uuid": "<uuid>"
}
```

**Логика `/add_user`:**

1. File lock.
2. Читать **`/usr/local/etc/xray/config.json`**.
3. Проверить `len(clients) - reserved < 50`.
4. Проверить уникальность UUID / email; если UUID есть — обновить `limit` (смена тарифа).
5. Добавить/обновить client в `inbounds[].settings.clients`.
6. Atomic write.
7. `xray run -test -c /usr/local/etc/xray/config.json`.
8. **`systemctl restart xray`**.
9. Return `{ "uuid", "email", "limit", "connection_uri" }`.

**Логика `/remove_user`:**

1. Lock → read → remove client by uuid → write → test → **`systemctl restart xray`**.
2. **Не удалять** clients из `AGENT_RESERVED_EMAILS`.

**Env Agent:**

| Переменная | Значение |
|------------|----------|
| `XRAY_CONFIG_PATH` | **`/usr/local/etc/xray/config.json`** |
| `XRAY_INBOUND_TAG` | `vless-reality-in` |
| `XRAY_MAX_USERS` | `50` |
| `XRAY_RELOAD_CMD` | **`systemctl restart xray`** |
| `XRAY_PUBLIC_HOST` | **`45.93.137.80`** |
| `AGENT_API_KEY` | секрет |
| `AGENT_ALLOWED_IPS` | **`37.230.114.25`** |
| `AGENT_PORT` | **`8443`** |
| `AGENT_RESERVED_EMAILS` | email/uuid личного VPN (не в лимите 50, не удалять) |

### 4.4 Xray Client (биллинг-сервер, Россия)

| Метод | HTTP |
|-------|------|
| `add_user(email, uuid, limit)` | `POST /add_user` |
| `remove_user(uuid)` | `POST /remove_user` |
| `get_users_count()` | `GET /users/count` |
| `health_check()` | `GET /health` |

**Env:**

| Переменная | Значение |
|------------|----------|
| `XRAY_AGENT_URL` | **`https://45.93.137.80:8443`** |
| `XRAY_AGENT_API_KEY` | секрет |
| `XRAY_AGENT_VERIFY_SSL` | `false` (self-signed) |
| `XRAY_MAX_USERS` | `50` |

### 4.5 Бизнес-правила

1. **Лимит 50 ключей** на Agent и в БД.
2. Один UUID на пользователя (MVP).
3. `email` в config = `user_{id}@netagent.local`.
4. `limit` в config = `plan.device_limit` при создании/продлении.
5. Audit log в NetAgent + лог Agent.

### 4.6 Ограничение устройств

**Реализация MVP:** только поле **`limit`** в Xray client. Xray ограничивает число одновременных подключений.

| Не в MVP | |
|----------|--|
| Stats API / polling online | ❌ |
| Статус `suspended` по device_limit | ❌ |
| Отдельный мониторинг соединений | ❌ |

### 4.7 Тестирование

- Unit-тесты Agent: mock config file, add/remove/count.
- Unit-тесты Client: mock HTTP.
- Интеграционные тесты на staging VPN.
- CLI: `scripts/xray_cli.py` — add/remove/list через Agent API.

---

## 5. Тарифы и оплата

### 5.1 Тарифы (таблица `plans`)

Только **месячная** подписка (30 дней). Цены зафиксированы в seed; редактируемы из админки.

| slug | name | device_limit | price_rub | description (UI) |
|------|------|--------------|-----------|------------------|
| `start` | **Start** | **1** | **150 ₽** | Для одного телефона |
| `standard` | **Standard** | **2** | **250 ₽** | Телефон + ноутбук |
| `family` | **Family** | **3** | **350 ₽** | Вся семья / все устройства |

В боте и на лендинге отображать: название, цену, описание и лимит устройств.

**Ограничения:**

- Нет тарифов на 3/6/12 месяцев в MVP.
- Нет тарифов с device_limit > 3 в MVP.
- При покупке пользователь **выбирает один из трёх тарифов** (1 / 2 / 3 устройств).

- При покупке пользователь выбирает **Start / Standard / Family**.
- `device_limit` в БД = `limit` в Xray config.

### 5.2 Mock-оплата (этапы разработки до production)

**На этапах 2–5** реальная оплата **не используется**. Вместо ЮKassa — **имитация оплаты**.

| Параметр | Значение |
|----------|----------|
| Env | `PAYMENT_PROVIDER=mock` |
| Интерфейс | `PaymentProvider` — абстракция; `MockPaymentProvider` + позже `YooKassaProvider` |

**Сценарии mock:**

1. **Бот:** кнопка «Оплатить (тест)» → мгновенный `payment.succeeded` без внешнего redirect.
2. **ЛК / API:** `POST /api/v1/payments/mock` — создать и подтвердить платёж в одном шаге.
3. **Админка:** ручное подтверждение `pending` payment.

**Flow (mock):**

```
User → выбор тарифа → payment (pending)
    → mock confirm → payment.succeeded
    → subscription.active, device_limit = plan.device_limit
    → POST /add_user { uuid, email, limit } → ключ пользователю
```

При ошибке Agent — `pending_activation`, retry job (без refund в mock).

### 5.3 ЮKassa (финальный этап — после домена)

**Порядок:** домен + HTTPS → ЮKassa → замена `PAYMENT_PROVIDER=yookassa`.

| Параметр | Env |
|----------|-----|
| Shop ID | `YOOKASSA_SHOP_ID` |
| Secret Key | `YOOKASSA_SECRET_KEY` |
| Return URL | `YOOKASSA_RETURN_URL` |
| Webhook | `POST /api/v1/payments/webhook/yookassa` |

Flow как в mock, но шаг confirm — redirect ЮKassa + webhook. Интерфейс `PaymentProvider` тот же.

**Не в scope MVP до финального этапа:** онлайн-чеки 54-ФЗ (уточнить при подключении production).

### 5.4 Бизнес-правила подписок

| Правило | Решение |
|---------|---------|
| Длительность оплаты | **Только 1 месяц** за один платёж (нет «купить 3 месяца») |
| Продление / новая покупка | `expires_at = сегодня (MSK) + 30 дней` — **всегда**, без стака с текущим сроком |
| UUID / ключ | **Тот же UUID** при каждом продлении; connection URI не меняется |
| После истечения | Client удалён из Xray; при оплате — `/add_user` с **существующим** `xray_uuid` |
| Апгрейд (Start→Family) | Разрешён: полная цена выбранного тарифа, `limit` обновляется |
| Даунгрейд (Family→Start) | Разрешён при следующей оплате, полная цена тарифа |
| Пробный период | **Не предоставляем** |
| Возвраты | Не в MVP; ручной refund через админку (post-MVP) |
| Часовой пояс | **Europe/Moscow (MSK)** для `starts_at`, `expires_at`, scheduler |

**Логика при успешной оплате:**

```
expires_at = now_MSK() + timedelta(days=30)
device_limit = plan.device_limit
subscription.plan_id = выбранный план

если client в Xray отсутствует (новый или истёк):
    POST /add_user { uuid: subscription.xray_uuid, email, limit }
если client есть (продление / смена тарифа):
    POST /add_user { uuid, email, limit }  # upsert, обновить limit
```

**Ограничение:** API не создаёт платёж с `duration > 30` или `quantity > 1` месяца.

### 5.5 Продление (сводка)

- Один платёж = один месяц; тариф можно сменить (апгрейд/даунгрейд).
- Срок всегда от «сегодня», ключ (UUID) сохраняется.

---

## 6. Модуль 2 — Telegram-бот

**Приоритет:** **Этап 5** (финальный, вместе с брендом и ЮKassa)  
**До этапа 5:** покупка/продление через **API**, **админку** и **ЛК** (mock).

**Путь:** `src/bot/`  
**Стек:** aiogram 3.x

### 6.1 Этапы разработки бота

| Этап | Содержание |
|------|------------|
| 2–4 | Stub / mock: placeholder-тексты, без финального бренда |
| **5** | Реальный бот: username, название, поддержка, ЮKassa redirect |

### 6.2 Функциональность (финальный этап)

| Функция | Описание |
|---------|----------|
| `/start` | Приветствие, CTA «Купить подписку» |
| Покупка | Выбор тарифа → **mock-оплата** (кнопка «Оплатить (тест)») |
| Продление | Выбор тарифа → mock-оплата |
| Мой ключ | Connection URI + QR |
| Статус | Тариф, лимит устройств, срок |

### 6.3 Сценарий покупки (mock → ЮKassa на этапе 5)

```
Пользователь → «Купить» → Start / Standard / Family
    → Проверка лимита 50 → payment (pending)
    → «Оплатить (тест)» → payment.succeeded
    → subscription (active), device_limit = plan.device_limit
    → Agent /add_user { limit } → ключ в бот
```

При ошибке Agent — `pending_activation`, retry.

### 6.4 Связь с БД

- `users.telegram_id` — уникальный ключ.
- Один Telegram-аккаунт = один `user`.

---

## 7. Модуль 3 — Панель администратора

**Приоритет:** Этап 3  
**Путь:** `src/admin/` + `src/api/`

### 7.1 Функциональность MVP

**Принцип:** без push-алертов и уведомлений админу. Вся операционная информация — **в админ-панели** (страницы со списками и дашборд).

#### Дашборд (обзор сервиса)
- Активные подписки / лимит 50 (без reserved).
- Новые пользователи за период.
- Выручка / начисления за период (mock → ЮKassa).
- Разбивка по тарифам Start / Standard / Family.
- Состояние связи с Agent (health, опционально).

#### Пользователи
- Список с фильтрами (активен, истёк, заблокирован).
- Карточка: Telegram ID, email, подписка, ключ (маскированный), `limit`, срок.
- Действия: блокировка, ручное продление, смена тарифа / `device_limit`.

#### Начисления / платежи
- Список всех payments: дата, пользователь, тариф, сумма, статус, provider.
- Фильтр по статусу (`pending`, `succeeded`, `pending_activation`, `failed`).
- Ручное подтверждение mock-платежа.

#### Подписки
- Список, ручное создание, reconcile БД ↔ Agent config.

#### Тарифы
- CRUD `plans`: цена, device_limit (1–3), is_active.

#### Администратор
- **Один** admin в MVP: seed **`adkharlamov.dev@gmail.com`** (`ADMIN_SEED_PASSWORD` из env).
- Без CRUD дополнительных admin-ов в MVP.

#### Аудит
- Лог действий (опционально, минимальный — ключевые операции).

---

## 8. Модуль 4 — Лендинг и личный кабинет

**Приоритет:** Этап 4  
**Путь:** `src/web/`

### 8.1 URL и домен

- **Лендинг / ЛК / webhook ЮKassa:** российский сервер.
- **Домен:** позже; до домена `WEB_BASE_URL` = `http://37.230.114.25`.
- **VPN-ссылки для пользователей:** всегда `45.93.137.80` (Литва), не домен.

### 8.2 Лендинг

| Блок | Содержание |
|------|------------|
| Hero | УТП, CTA |
| Тарифы | **3 карточки**: Start / Standard / Family (цена и описание из БД) |
| FAQ | v2rayN, Hiddify, Streisand |
| Footer | Контакты |

### 8.3 Личный кабинет

- Обзор подписки, connection URI, QR.
- Покупка / продление — mock-оплата (ЮKassa на финальном этапе).
- Отображение лимита устройств по тарифу.

---

## 9. Модель данных (PostgreSQL)

### 9.1 Таблицы MVP

```sql
-- Пользователи (клиенты VPN)
users (
  id              BIGSERIAL PRIMARY KEY,
  email           VARCHAR(255) UNIQUE,
  password_hash   VARCHAR(255),
  telegram_id     BIGINT UNIQUE,
  status          VARCHAR(20) DEFAULT 'active',
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
)

-- Тарифы: только месячные, device_limit 1–3
plans (
  id              SERIAL PRIMARY KEY,
  slug            VARCHAR(50) UNIQUE NOT NULL,  -- start, standard, family
  name            VARCHAR(100) NOT NULL,        -- Start, Standard, Family
  description     VARCHAR(255),               -- текст для UI
  duration_days   INT DEFAULT 30,
  price_rub       DECIMAL(10,2) NOT NULL,
  device_limit    INT NOT NULL CHECK (device_limit BETWEEN 1 AND 3),
  is_active       BOOLEAN DEFAULT TRUE,
  sort_order      INT DEFAULT 0
)

-- Подписки
subscriptions (
  id              BIGSERIAL PRIMARY KEY,
  user_id         BIGINT REFERENCES users(id),
  plan_id         INT REFERENCES plans(id),
  status          VARCHAR(20),            -- pending, active, expired,
                                          -- cancelled, pending_activation
                                          -- (suspended — не используется в MVP)
  xray_email      VARCHAR(255) UNIQUE,
  xray_uuid       UUID UNIQUE,
  device_limit    INT NOT NULL CHECK (device_limit BETWEEN 1 AND 3),
  starts_at       TIMESTAMPTZ,
  expires_at      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ DEFAULT NOW()
)

-- Платежи (ЮKassa)
payments (
  id              BIGSERIAL PRIMARY KEY,
  user_id         BIGINT REFERENCES users(id),
  subscription_id BIGINT REFERENCES subscriptions(id),
  plan_id         INT REFERENCES plans(id),
  provider        VARCHAR(50) DEFAULT 'mock',  -- mock | yookassa
  external_id     VARCHAR(255) UNIQUE,    -- YooKassa payment id
  amount          DECIMAL(10,2),
  currency        VARCHAR(3) DEFAULT 'RUB',
  status          VARCHAR(20),            -- pending, succeeded, failed, refunded
  confirmation_url VARCHAR(512),
  created_at      TIMESTAMPTZ DEFAULT NOW()
)

-- admin_users (seed)
admin_users (
  id              SERIAL PRIMARY KEY,
  email           VARCHAR(255) UNIQUE,
  password_hash   VARCHAR(255),
  role            VARCHAR(20) DEFAULT 'admin',
  created_at      TIMESTAMPTZ DEFAULT NOW()
)
-- Seed: adkharlamov.dev@gmail.com (ADMIN_SEED_PASSWORD из env)
```

### 9.2 Seed данных (plans)

При первом запуске создать 3 плана:

```sql
INSERT INTO plans (slug, name, description, duration_days, price_rub, device_limit, sort_order) VALUES
  ('start',    'Start',    'Для одного телефона',           30, 150.00, 1, 1),
  ('standard', 'Standard', 'Телефон + ноутбук',             30, 250.00, 2, 2),
  ('family',   'Family',   'Вся семья / все устройства',    30, 350.00, 3, 3);
```

### 9.3 Индексы

- `subscriptions(user_id)`, `subscriptions(status)`, `subscriptions(expires_at)`
- `payments(user_id)`, `payments(status)`, `payments(external_id)`
- `users(telegram_id)`, `users(email)`
- `plans(device_limit)` WHERE `is_active`

---

## 10. Этапы разработки

> **ЮKassa и домен — последний этап.** До этого везде mock-оплата.

### Этап 0 — Подготовка (1–2 дня)

- [ ] Структура репозитория
- [ ] Docker Compose: postgres, api (заглушка)
- [ ] Alembic, `.env.example`, README
- [ ] `docker-compose.yml` (Россия) + `docker-compose.vpn.yml` (Литва)

### Этап 1 — Xray Agent + Client (4–6 дней)

- [ ] FastAPI Agent: `/add_user`, `/remove_user`, port 8443, self-signed HTTPS
- [ ] Правка `/usr/local/etc/xray/config.json`, поле `limit`, restart xray
- [ ] HTTP-клиент на российском сервере
- [ ] CLI, тесты

**Критерий:** add_user с limit=1/2/3, подключение, remove_user.

### Этап 2 — API Core + Mock-оплата (4–6 дней)

- [ ] FastAPI: users, subscriptions, plans, payments
- [ ] `MockPaymentProvider`, правила продления (MSK, now+30, same UUID)
- [ ] Seed тарифов; expire → `/remove_user` (не трогать reserved)
- [ ] Retry `pending_activation`
- [ ] Покупка через API / админку (без финального бота)

**Критерий:** mock-оплата → подписка + ключ с правильным `limit`.

### Этап 3 — Админ-панель (4–6 дней)

- [ ] Seed admin `adkharlamov.dev@gmail.com`
- [ ] CRUD тарифов, дашборд, reconcile, ручное подтверждение payment

### Этап 4 — Лендинг + ЛК (4–6 дней)

- [ ] Лендинг и ЛК с **mock-брендом** (placeholder название/стили)
- [ ] Регистрация, mock-оплата
- [ ] `http://37.230.114.25`

### Этап 5 — Бот + бренд + домен + ЮKassa (финальный, 4–6 дней)

- [ ] Домен, HTTPS (Let's Encrypt)
- [ ] Финальный бренд (название, логотип, тексты)
- [ ] Telegram-бот (реальный username, поддержка)
- [ ] `YooKassaProvider`, webhook
- [ ] Оферта / политика (если нужны)

### Этап 6 — Стабилизация (2–3 дня)

- [ ] E2E критических сценариев
- [ ] Health-endpoints, логи
- [ ] Документация деплоя

---

## 11. Фоновые задачи (scheduler)

| Задача | Период | Действие |
|--------|--------|----------|
| `expire_subscriptions` | 15 мин | `expires_at < now_MSK` → expired → `/remove_user` (skip reserved) |
| `retry_pending_activation` | 5 мин | повтор `/add_user` |
| `reconcile_agent` | сутки | БД ↔ config clients |
| `low_subscription_warning` | день | за 3 дня до истечения |

**Не в MVP:** `check_device_limits`, `sync_traffic` (Stats).

---

## 12. Безопасность

| Требование | Реализация |
|------------|------------|
| Секреты | `.env`, не в git |
| Xray Agent | API key + IP whitelist + self-signed HTTPS :8443 |
| Reality privateKey | Только на VPN-сервере |
| ЮKassa webhook | Финальный этап (подпись / IP) |
| Пароли | bcrypt |
| HTTPS | Production: API, web, Agent |
| Ключи в UI | Маскирование |

---

## 13. Структура репозитория (целевая)

```
NetAgent/
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.bot
│   ├── Dockerfile.xray-agent
│   ├── docker-compose.yml          # Россия: postgres, api, bot, web, admin
│   └── docker-compose.vpn.yml      # Литва: xray-agent (xray — systemd)
├── docs/
│   └── TZ.md
├── migrations/
├── scripts/
│   └── xray_cli.py
├── src/
│   ├── api/
│   ├── bot/
│   ├── admin/
│   ├── web/
│   ├── core/
│   ├── xray_agent/      # микросервис (деплой на VPN)
│   └── xray_client/     # HTTP-клиент для NetAgent
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

---

## 14. Зафиксированные параметры (сводка)

| Параметр | Значение |
|----------|----------|
| VPN (Литва) | `45.93.137.80` |
| App (Россия) | `37.230.114.25` |
| Agent URL | `https://45.93.137.80:8443` |
| Config Xray | `/usr/local/etc/xray/config.json` |
| Reload | `systemctl restart xray` |
| Device limit | Xray `limit` 1/2/3 |
| Тарифы | Start 150₽ / Standard 250₽ / Family 350₽ |
| Оплата (dev) | **mock** |
| Оплата (prod) | ЮKassa — **этап 5** |
| Лимит ключей | 50 (без reserved admin client) |
| Продление | MSK, всегда today+30, same UUID |
| Первый admin | `adkharlamov.dev@gmail.com` (один) |
| Алерты | Нет — только админ-панель |
| Backup БД | Не в MVP |
| Бот / бренд | Этап 5 |

## 15. Вопросы для финализации ТЗ

Перед началом разработки нужно закрыть пункты в **15.3** (домен, ЮKassa, бот, бренд — этап 5). Для **Этапа 1** ТЗ достаточно.

### 15.1 Закрыто в v1.5

| # | Вопрос | Решение |
|---|--------|---------|
| B1 | Продление | ✅ Всегда **сегодня (MSK) + 30 дней** |
| B2 | UUID после истечения | ✅ **Тот же UUID** |
| B3 | Апгрейд тарифа | ✅ Разрешён, полная цена плана |
| B4 | Даунгрейд | ✅ Разрешён при следующей оплате |
| B5 | Пробный период | ✅ **Нет** |
| B6 | Мульти-месяц | ✅ **Нельзя** — только 1 месяц за платёж |
| B7 | Тестовый client | ✅ **Оставить**; reserved, не в лимите 50 |
| B8 | Часовой пояс | ✅ **MSK** (`Europe/Moscow`) |
| A1 | Первый admin | ✅ `adkharlamov.dev@gmail.com` |
| A2 | Количество admin | ✅ **Один** |
| A3 | Алерты | ✅ **Не нужны**; информация в админке |
| I2 | Backup PostgreSQL | ✅ **Не в MVP** |
| T/C | Бот и бренд | ✅ Mock до **этапа 5** |

### 15.2 Закрыто в v1.4

| # | Вопрос | Решение |
|---|--------|---------|
| K3 | Порт / TLS Agent | ✅ `8443`, self-signed HTTPS, `X-API-Key` |
| K4 | Путь config | ✅ `/usr/local/etc/xray/config.json` |
| K5 | Лимит устройств | ✅ Xray `limit`; без мониторинга/suspension |
| K6 | Оплата на этапе разработки | ✅ Mock; ЮKassa — этап 5 |
| K7 | WireGuard / прокси | ✅ Не в scope |

### 15.3 Отложено до финального этапа (этап 5)

| # | Вопрос |
|---|--------|
| K1 | Домен + HTTPS |
| K2 | ЮKassa + онлайн-чеки 54-ФЗ |
| T1–T3 | Telegram-бот (username, поддержка) |
| C1–C3 | Бренд, оферта, логотип |

### 15.4 Опционально (не блокирует)

| # | Вопрос |
|---|--------|
| I1 | Inbound tag `vless-reality-in` |
| I3 | Расширенный мониторинг / alerting (post-MVP) |
| I4 | `fp=chrome` в VLESS-ссылке |

### 15.5 Отложено (post-MVP)

| # | Вопрос |
|---|--------|
| D1 | Связка TG ↔ web |
| D2 | Stats API, online-мониторинг |
| D3 | WireGuard, другие протоколы |
| D4 | Multi-month тарифы |

### 15.6 Статус закрытых вопросов

| # | Вопрос | Статус |
|---|--------|--------|
| 1–13 | v1.2–1.4 | ✅ |
| 14 | Бизнес-правила подписок | ✅ v1.5 |
| 15 | Admin seed email | ✅ |
| 16 | Бот/бренд отложены | ✅ этап 5 |
| 17 | Один admin, без алертов, без backup | ✅ v1.6 |

---

## 16. Переменные окружения (сводка)

### Российский сервер (`api`, `bot`, `web`)

| Переменная | Пример / значение |
|------------|-------------------|
| `DATABASE_URL` | `postgresql://...@localhost:5432/netagent` |
| `XRAY_AGENT_URL` | `https://45.93.137.80:8443` |
| `XRAY_AGENT_VERIFY_SSL` | `false` |
| `XRAY_AGENT_API_KEY` | секрет |
| `XRAY_PUBLIC_HOST` | `45.93.137.80` |
| `XRAY_MAX_USERS` | `50` |
| `PAYMENT_PROVIDER` | **`mock`** (этап 5: `yookassa`) |
| `TIMEZONE` | **`Europe/Moscow`** |
| `ADMIN_SEED_EMAIL` | **`adkharlamov.dev@gmail.com`** |
| `ADMIN_SEED_PASSWORD` | задаётся при деплое |
| `WEB_BASE_URL` | `http://37.230.114.25` |

### Литовский сервер (`xray-agent`)

| Переменная | Пример / значение |
|------------|-------------------|
| `XRAY_CONFIG_PATH` | **`/usr/local/etc/xray/config.json`** |
| `XRAY_RELOAD_CMD` | `systemctl restart xray` |
| `XRAY_PUBLIC_HOST` | `45.93.137.80` |
| `XRAY_MAX_USERS` | `50` |
| `AGENT_API_KEY` | секрет |
| `AGENT_ALLOWED_IPS` | **`37.230.114.25`** |
| `AGENT_PORT` | **`8443`** |
| `AGENT_RESERVED_EMAILS` | email/uuid личного VPN |

*(ЮKassa, `TELEGRAM_BOT_TOKEN` — этап 5)*

---

## 17. Критерии приёмки MVP

### Этапы 1–4 (до бота/ЮKassa)

1. Не более **50** paying clients (reserved admin client исключён).
2. Продление: **MSK**, **today + 30 days**, **same UUID**.
3. Апгрейд/даунгрейд тарифа при оплате; **нет** multi-month и trial.
4. Mock-оплата через API / админку / ЛК.
5. Xray `limit` = 1/2/3; ключ на `45.93.137.80`.
6. Admin seed: `adkharlamov.dev@gmail.com`.
7. Истечение → `/remove_user` (reserved не трогать).

### Этап 5 (production)

8. Домен + HTTPS.
9. Финальный **бот и бренд**.
10. **ЮKassa** вместо mock.
11. Оферта / политика (если требуются).

---

## 18. Post-MVP

- Stats API / online-мониторинг (альтернатива или дополнение к `limit`)
- gRPC hot-add
- Тарифы 3/6/12 месяцев
- TG ↔ web linking
- Несколько VPN-нод
- WireGuard и другие протоколы (явно не в scope MVP)

---

*Документ является основным ориентиром для разработки. Изменения — через обновление версии ТЗ.*
