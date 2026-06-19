# Вход через Россию (relay на Литву)

Когда с **LTE** не работает прямой вход на `45.93.137.80`, а с Wi‑Fi работает — оператор часто режет **зарубежные IP**. Сайт [alexkharlamov.ru](https://alexkharlamov.ru/) с телефона может открываться, потому что он на **домене** (часто через Cloudflare), а не как «голый» IP в ping.pe.

**Пошаговая установка с командами:** [deploy-russia-relay-walkthrough.md](deploy-russia-relay-walkthrough.md)

**Схема:** телефон → **37.230.114.25:443** (Xray Россия) → **45.93.137.80:443** (Xray Литва, выход в интернет). IP Литвы не меняем.

## Проверка на iPhone (без ping.pe)

1. Установите **Streisand** или **v2rayTun**.
2. После настройки России импортируйте VLESS-ссылку с host `37.230.114.25`.
3. **Wi‑Fi выключить**, только LTE → подключить.

Это единственный надёжный тест с iPhone. ping.pe и браузер на `http://IP:443` не показыают доступность VLESS.

---

## Шаг 0. Порт 443 на России

```bash
ss -lntp | grep ':443'
```

| Что слушает 443 | Действие |
|-----------------|----------|
| Пусто | Xray на 443 — ок |
| **nginx** (сайт) | Вариант A: сайт только через Cloudflare, на origin оставить 443 для Xray. Вариант B: Xray на **2053** и проверить LTE (иногда проходит). Вариант C: `stream` в nginx по SNI — сложнее |
| docker | Разобрать, что в контейнере |

---

## Шаг 1. Литва — UUID «моста»

На `45.93.137.80`:

```bash
sudo systemctl stop netagent-xray-agent
BRIDGE_UUID=$(xray uuid)
echo "BRIDGE_UUID=$BRIDGE_UUID"   # сохраните
```

В `/usr/local/etc/xray/config.json` в `clients` добавьте (не удаляя остальных):

```json
{
  "id": "BRIDGE_UUID",
  "flow": "xtls-rprx-vision",
  "email": "bridge_russia"
}
```

```bash
sudo xray run -test -c /usr/local/etc/xray/config.json
sudo chmod 644 /usr/local/etc/xray/config.json
sudo systemctl restart xray
```

Публичный ключ Литвы (для outbound на России):

```bash
xray x25519 -i "eGdm5HgRgqJFCfq-SNUhbeRw35bqGCUd3l81X0xRS3g"
# Password = privateKey → Public key = pbk для outbound
```

Запишите **Public key** (pbk Литвы) и **BRIDGE_UUID**.

В `xray-agent.env` на Литве добавьте мост в reserved (не удалять через API):

```env
AGENT_RESERVED_EMAILS=...,bridge_russia
AGENT_RESERVED_UUIDS=...,BRIDGE_UUID
```

---

## Шаг 2. Россия — ключи Reality (новые, не Литва)

На `37.230.114.25`:

```bash
xray x25519
# PrivateKey → в inbound realitySettings.privateKey
# Password    → REALITY_PUBLIC_KEY для ссылок пользователей (pbk России)
```

Сгенерируйте UUID для своего телефона (или используйте существующий):

```bash
xray uuid
```

---

## Шаг 3. Конфиг Xray на России

Скопируйте шаблон из репозитория:

```bash
sudo cp /opt/netagent/configs/xray-russia-relay.example.json \
  /usr/local/etc/xray/config.json
sudo nano /usr/local/etc/xray/config.json
```

Подставьте:

| Поле | Значение |
|------|----------|
| inbound clients `id` | UUID вашего телефона |
| inbound `privateKey` | PrivateKey России |
| outbound user `id` | BRIDGE_UUID |
| outbound `publicKey` | pbk **Литвы** |
| `shortId` | `6ba85179e30d4fc2` (как на Литве) |

Если 443 занят nginx — в inbound смените `port` на `2053` и в ссылке порт `2053`.

```bash
sudo xray run -test -c /usr/local/etc/xray/config.json
sudo systemctl enable xray
sudo systemctl restart xray
sudo ufw allow 443/tcp    # или 2053/tcp
```

---

## Шаг 4. VLESS-ссылка для iPhone (LTE)

На России:

```bash
cd /opt/netagent
python scripts/build_relay_vless_link.py \
  --host 37.230.114.25 \
  --port 443 \
  --uuid YOUR_PHONE_UUID \
  --pbk PBK_RUSSIA \
  --sid 6ba85179e30d4fc2 \
  --name "NetAgent-RU"
```

Импорт в Streisand → LTE без Wi‑Fi.

Параметры ссылки:

- **Host:** `37.230.114.25` (не Литва)
- **pbk:** публичный ключ **России**
- **uuid:** клиент на **inbound России**
- **sni / flow / sid:** как в inbound России

---

## Шаг 5. Бот NetAgent (после успешного LTE-теста)

В `.env` на России:

```env
XRAY_PUBLIC_HOST=37.230.114.25
REALITY_PUBLIC_KEY=<pbk России>
REALITY_SHORT_ID=6ba85179e30d4fc2
REALITY_SNI=www.wikipedia.org
```

Xray-agent остаётся на **Литве** — он добавляет клиентов в exit-сервер. Мост `bridge_russia` только вручную, в reserved.

Пользователи получают ссылки на **Россию**; трафик выходит через Литву.

---

## Если LTE на Россию тоже не работает

1. Порт **2053** / **8443** вместо 443 на inbound России.
2. Сайт на Cloudflare — **не** спасёт VLESS на тот же IP: VPN = TCP к IP сервера, не HTTP через CF.
3. Другий хостинг/провайдер в РФ с другим IP (без смены IP Литвы).
4. Fragment в Streisand (Settings → Fragment) на ссылке России.

---

## Диагностика relay

На России:

```bash
journalctl -u xray -n 50 --no-pager
```

На Литве при подключении с телефона должны быть сессии с IP `37.230.114.25` (мост), не с IP вашего LTE напрямую.
