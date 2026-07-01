# Ограничение ключей и провизионирование через бота

Как не дать пользователям делиться одним ключом, и как бот добавляет клиентов в Xray.

См. также: [device-enforcement.md](device-enforcement.md) (настройка monitor), [deploy-relay.md](deploy-relay.md) (схема relay).

---

## Два разных лимита

| Лимит | Что значит | Где проверяется |
|-------|------------|-----------------|
| **Трафик (`traffic_limit_gb`)** | Сколько ГБ можно скачать/отдать за месяц подписки | `device_monitor` + Xray Stats API |
| **Sharing** | Один ключ могут скопировать друзьям — трафик сгорит быстрее; при превышении лимита ключ отключается | тот же monitor |

Лимит «N устройств / N слотов» **убран** — он не мешал делиться одним ключом.

---

## Модель ключа

- **Один ключ** на VPN-подписку (email `{telegram_id}_vpn`)
- Создаётся **автоматически при оплате**
- Кнопка **«Новый ключ»** — если ключ могли скопировать (старый перестаёт работать)
- Тарифы отличаются **объёмом трафика**, не числом слотов:

| Тариф | ГБ/мес |
|-------|--------|
| Connect | 50 |
| Connect+ | 100 |
| Combo | 80 |
| Combo Max | 200 |

---

## Варианты ограничения (сравнение)

### 1. Поле `limit` в client Xray — не используем

В чистом Xray-core поле `limit` в `settings.clients[]` **не ограничивает** число одновременных подключений так, как ожидается. В нашем `xray-agent` оно **намеренно не пишется** в config (`config_service._sanitize_clients`).

**Вердикт:** не полагаться на `limit` для anti-sharing.

### 2. Stats API + monitor (рекомендуется, уже в проекте)

- Каждому устройству — свой UUID и `email` вида `{telegram_id}_{suffix}` (нужен для Stats).
- Сервис **monitor** (Docker на России) каждые 30 сек опрашивает `GET /stats/users_online`.
- Если у одного email **> 1 IP онлайн** или IP из **разных стран** → ключ удаляется из Xray, в БД `status=suspended`.

**Плюсы:** работает с любым клиентом (v2rayNG, Streisand, Hiddify).  
**Минусы:** нужен Stats API в config Xray; возможны ложные срабатывания при смене IP (LTE ↔ Wi‑Fi).

### 3. Один ключ на всю подписку + monitor

Один UUID на пользователя, `limit` в продукте = «сколько устройств по тарифу», но технически один ключ. Monitor режет sharing.

**Минусы:** пользователь не может раздать разные ключи семье; сложнее UX.  
**Вердикт:** не используем — у нас **отдельный UUID на каждое устройство**.

### 4. Жёсткий лимит только в боте (без monitor)

Только `device_limit` в тарифе, без Stats.

**Минусы:** пользователь может скопировать один VLESS-ключ на 10 телефонов.  
**Вердикт:** только для dev/MVP без enforcement — **не для продакшена**.

---

## Архитектура (как сейчас)

```
Пользователь Telegram
        │
        ▼
┌─────────────────── Россия (37.230.114.25) ───────────────────┐
│  bot          — оплата, добавление устройства                 │
│  XrayProvisioner ──POST /add_user──────────────────┐          │
│  monitor      — Stats, suspend при sharing        │          │
│  postgres     — users, subscriptions, devices     │          │
└───────────────────────────────────────────────────│──────────┘
                                                    │ HTTPS :8443
                                                    ▼
┌─────────────────── Entry (relay) или Литва ──────────────────┐
│  xray-agent   — правит config.json, restart xray             │
│  xray         — VLESS Reality, Stats API :10085              │
└──────────────────────────────────────────────────────────────┘
```

### Важно: relay vs прямой Литва

| Режим | Где xray-agent | `XRAY_INBOUND_TAG` | `XRAY_PUBLIC_HOST` | Stats / monitor |
|-------|----------------|--------------------|--------------------|-----------------|
| **Relay (LTE)** | **Россия** `51.250.112.128` | `users-in` | `51.250.112.128` | На **entry**-сервере |
| **Прямой exit** | Литва `45.93.137.80` | `vless-reality-in` | `45.93.137.80` | На Литве |

При relay пользователь подключается к **entry** (`:2053`), клиенты должны быть в `configs/russia-relay.json`, не только на Литве.  
`REALITY_PUBLIC_KEY` в `.env` бота — **pbk того inbound, куда подключается клиент** (для relay — ключ России).

---

## Поток в боте (покупка → ключ)

```
1. Оплата (mockpay)
   └─► subscription в Postgres (device_limit = 1/2/3)
       ключ в Xray НЕ создаётся

2. «Добавить устройство» → iPhone / Android / …
   └─► BillingClient.add_device()
         ├─► uuid4 + email = "{telegram_id}_phone"
         ├─► XrayProvisioner.provision_key() → POST /add_user
         ├─► INSERT devices
         └─► VLESS-ссылка в «Моя подписка»

3. Если Postgres упал после add_user
   └─► rollback: remove_user(uuid)
```

Код:

- `src/bot/xray_provisioner.py` — обёртка над xray-agent
- `src/bot/billing.py` — `add_device` / `remove_device`
- `src/xray_agent/config_service.py` — запись в config + `systemctl restart xray`

---

## Шаг 1. xray-agent на сервере с user-inbound

### Relay (рекомендуется для мобильного)

На **51.250.112.128**:

1. Config: `configs/russia-relay.json` → `/usr/local/etc/xray/config.json`
2. Добавить Stats API (см. [device-enforcement.md](device-enforcement.md))
3. Деплой agent: [deploy-lithuania.md](deploy-lithuania.md) — те же шаги, но на **России**

`xray-agent.env` (пример):

```env
XRAY_CONFIG_PATH=/usr/local/etc/xray/config.json
XRAY_INBOUND_TAG=users-in
XRAY_MAX_USERS=50
XRAY_RELOAD_CMD=systemctl restart xray
XRAY_PUBLIC_HOST=51.250.112.128
XRAY_PUBLIC_PORT=2053
REALITY_PUBLIC_KEY=<pbk России из inbound>
REALITY_SHORT_ID=6ba85179e30d4fc2
REALITY_SNI=www.wikipedia.org
AGENT_API_KEY=<секрет>
AGENT_ALLOWED_IPS=37.230.114.25
XRAY_API_SERVER=127.0.0.1:10085
XRAY_BIN=/usr/local/bin/xray
```

Проверка с app-сервера:

```bash
curl -k -H "X-API-Key: $KEY" https://51.250.112.128:8443/health
curl -k -H "X-API-Key: $KEY" https://51.250.112.128:8443/users/count
```

### Прямой Литва

Agent на `45.93.137.80`, tag `vless-reality-in`, порт 443 — см. [deploy-lithuania.md](deploy-lithuania.md).

---

## Шаг 2. `.env` бота (Россия)

```env
# Куда стучится бот за add_user / remove_user
XRAY_AGENT_URL=https://51.250.112.128:8443
XRAY_AGENT_API_KEY=<тот же AGENT_API_KEY>
XRAY_AGENT_VERIFY_SSL=false

# Что попадает в VLESS-ссылку пользователю
XRAY_PUBLIC_HOST=51.250.112.128
XRAY_PUBLIC_PORT=2053
REALITY_PUBLIC_KEY=<pbk entry inbound>
REALITY_SHORT_ID=6ba85179e30d4fc2
REALITY_SNI=www.wikipedia.org
VLESS_FLOW=xtls-rprx-vision
```

Если `XRAY_AGENT_URL` пуст — бот в dev создаёт устройства только в БД (ключ в Xray не появится). В production URL **обязателен**.

---

## Шаг 3. Monitor (anti-sharing)

На app-сервере в `.env`:

```env
DEVICE_MONITOR_INTERVAL_SECONDS=30
DEVICE_MONITOR_MAX_ONLINE_IPS=1
GEOIP_DATABASE_PATH=/opt/netagent/geoip/GeoLite2-Country.mmdb
```

```bash
docker compose up -d --build
docker compose logs -f monitor
```

Monitor использует тот же `XRAY_AGENT_URL` — Stats должны быть на **том же Xray**, куда добавляются клиенты.

---

## Шаг 4. Проверка end-to-end

1. В боте: оплатить Connect → «Добавить устройство» → iPhone.
2. На entry-сервере:
   ```bash
   xray api statsonlineiplist -server=127.0.0.1:10085 -email "TELEGRAM_ID_phone"
   ```
3. Подключить телефон по VLESS — в Stats один IP.
4. Вставить тот же ключ на второй телефон — через ~30–60 сек monitor должен suspend (2 IP).

---

## API xray-agent (справка)

| Метод | Путь | Кто вызывает |
|-------|------|--------------|
| POST | `/add_user` | `XrayProvisioner` (бот) |
| POST | `/remove_user` | бот, monitor |
| GET | `/stats/users_online` | monitor |
| GET | `/health` | деплой, мониторинг |

Body `/add_user`:

```json
{
  "email": "544709692_phone",
  "uuid": "989e7ddf-acc4-4178-99d5-c3b4ea33a613",
  "limit": 1,
  "flow": "xtls-rprx-vision"
}
```

---

## Что ещё сделать (roadmap)

| Задача | Зачем |
|--------|-------|
| `expire_subscriptions` job | Удалять ключи при истечении подписки |
| Уведомление в Telegram при suspend | Пользователь понимает, почему отключилось |
| Debounce 2–3 poll перед suspend | Меньше ложных блокировок при смене IP |
| Показ suspended-устройств в боте | Можно удалить и создать новый ключ |
| Reconcile DB ↔ Xray | Админка / nightly diff |

---

## Быстрый чеклист

- [ ] Xray на entry (relay) или exit с Stats API
- [ ] xray-agent :8443, `AGENT_ALLOWED_IPS` = IP app-сервера
- [ ] В `.env` бота: `XRAY_AGENT_URL`, `XRAY_PUBLIC_HOST`, `REALITY_PUBLIC_KEY` **entry**
- [ ] `docker compose up` — bot + monitor
- [ ] Тест: add device → ключ в config → подключение → sharing → suspend
