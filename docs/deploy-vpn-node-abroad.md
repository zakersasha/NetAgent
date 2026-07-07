# Вторая exit-нода за рубежом (relay через Яндекс)

**Схема NetAgent:**

```
Клиент → entry (Яндекс / Россия) → exit #1 Литва (45.93.137.80:443)
                                 → exit #2 srv1541843 (2087)
```

Клиент **никогда** не подключается к IP зарубежного exit. В VLESS-ссылке всегда **host, port и Reality-ключи entry** (Яндекс). За рубежом — только **мост** (`bridge_russia`) и выход в интернет.

| Компонент | Сервер | Порт | Роль |
|-----------|--------|------|------|
| Entry | `51.250.112.128` (Яндекс) | `2053` (или `443` на `37.230.114.25`) | Вход для клиентов, xray-agent |
| Exit #1 | `45.93.137.80` (Литва) | `443` | Выход, мост `9783d565-…` |
| Exit #2 | `srv1541843` | `2087` | Выход, свой мост |
| Прокси бота | `45.93.137.80` | `3128` | Telegram/OpenAI — **не трогаем** |

Балансировка в боте: новый ключ → нода с минимумом активных устройств (`pick_vpn_node`). Разные exit-пулы — **разные inbound на entry** (разные порты, одни Reality-ключи entry).

---

## 1. Exit на новом сервере (`srv1541843`)

Xray на **2087** — это **только exit**. Порт **443** может быть занят Docker (`amnezia-xray`) — для NetAgent это нормально.

### 1.1 Проверка (у вас уже сделано)

```bash
systemctl status xray
ss -lntp | grep 2087
xray run -test -c /usr/local/etc/xray/config.json   # Configuration OK
curl -4 ifconfig.me   # сохраните IP — нужен для outbound на entry
```

Reality exit #2 (для outbound **с entry**, не для клиентских ссылок):

| Параметр | Значение |
|----------|----------|
| PrivateKey (config) | `AB3hjI-FdE0z3CFyqJhfr8MJvpVprz2AunP8u-zjO0g` |
| PublicKey / pbk | `WDqt_crB3vWrle5JQ4DmUm2PHuXTR9nhicu0jv3ySSY` |
| shortId | `56f8dc4a36e55951` |

### 1.2 Мост на exit (обязательно)

На exit **нет пользовательских UUID** — только admin + мост с entry:

```bash
BRIDGE2=$(xray uuid)
echo "BRIDGE2=$BRIDGE2"
```

В `/usr/local/etc/xray/config.json` в `clients` inbound на 2087:

```json
{
  "id": "BRIDGE2_UUID",
  "flow": "xtls-rprx-vision",
  "email": "bridge_russia_2"
}
```

```bash
xray run -test -c /usr/local/etc/xray/config.json
systemctl restart xray
```

**xray-agent на exit для пользователей не нужен.** Agent живёт на **entry** и пишет UUID в inbound `users-in` / `users-in-fi1`.

Firewall exit — **2087 только с IP entry** (не весь интернет):

```bash
ufw allow from 51.250.112.128 to any port 2087 proto tcp
# если entry также 37.230.114.25:
ufw allow from 37.230.114.25 to any port 2087 proto tcp
ufw deny 2087/tcp
```

---

## 2. Entry (Яндекс `51.250.112.128`) — второй путь к exit #2

Базовый config: `configs/russia-relay.json` (сейчас один inbound `users-in:2053` → `to-lithuania`).

### 2.1 Второй inbound для пула fi1

Добавьте inbound (порт **2096** — пример, любой свободный на entry):

```json
{
  "tag": "users-in-fi1",
  "listen": "0.0.0.0",
  "port": 2096,
  "protocol": "vless",
  "settings": { "clients": [], "decryption": "none" },
  "streamSettings": {
    "network": "tcp",
    "security": "reality",
    "realitySettings": {
      "show": false,
      "dest": "www.wikipedia.org:443",
      "serverNames": ["www.wikipedia.org"],
      "privateKey": "<privateKey entry — тот же что у users-in>",
      "shortIds": ["6ba85179e30d4fc2"]
    }
  },
  "sniffing": { "enabled": true, "destOverride": ["http", "tls", "quic"] }
}
```

### 2.2 Outbound на srv1541843

```json
{
  "tag": "to-fi1",
  "protocol": "vless",
  "settings": {
    "vnext": [{
      "address": "IP_srv1541843",
      "port": 2087,
      "users": [{
        "id": "BRIDGE2_UUID",
        "encryption": "none",
        "flow": "xtls-rprx-vision",
        "email": "bridge_russia_2"
      }]
    }]
  },
  "streamSettings": {
    "network": "tcp",
    "security": "reality",
    "realitySettings": {
      "serverName": "www.wikipedia.org",
      "publicKey": "WDqt_crB3vWrle5JQ4DmUm2PHuXTR9nhicu0jv3ySSY",
      "shortId": "56f8dc4a36e55951",
      "fingerprint": "chrome"
    }
  }
}
```

### 2.3 Routing

```json
"rules": [
  { "type": "field", "inboundTag": ["users-in"], "outboundTag": "to-lithuania" },
  { "type": "field", "inboundTag": ["users-in-fi1"], "outboundTag": "to-fi1" }
]
```

```bash
xray run -test -c /usr/local/etc/xray/config.json
systemctl restart xray
ss -lntp | grep -E '2053|2096'
```

---

## 3. xray-agent на entry (не на exit)

Два inbound → два agent (разные порты и `XRAY_INBOUND_TAG`):

| Пул | Agent URL | `XRAY_INBOUND_TAG` | `XRAY_PUBLIC_PORT` |
|-----|-----------|-------------------|-------------------|
| lt1 | `https://51.250.112.128:8443` | `users-in` | `2053` |
| fi1 | `https://51.250.112.128:8444` | `users-in-fi1` | `2096` |

Общее для обоих:

```env
XRAY_PUBLIC_HOST=51.250.112.128
REALITY_PUBLIC_KEY=<pbk entry inbound, не exit>
REALITY_SHORT_ID=6ba85179e30d4fc2
REALITY_SNI=www.wikipedia.org
AGENT_ALLOWED_IPS=37.230.114.25
```

Подробнее: [key-enforcement-guide.md](key-enforcement-guide.md), [deploy-russia-relay-walkthrough.md](deploy-russia-relay-walkthrough.md).

---

## 4. Запись в Postgres (Москва)

`public_host` / `public_port` / `reality_*` — **entry**, не exit.

```sql
-- исправить lt1, если seed migration 012 записал Литву напрямую:
UPDATE vpn_nodes SET
  public_host = '51.250.112.128',
  public_port = 2053,
  agent_url = 'https://51.250.112.128:8443',
  reality_public_key = '<pbk entry>',
  reality_short_id = '6ba85179e30d4fc2'
WHERE slug = 'lt1';

INSERT INTO vpn_nodes (
  slug, name, public_host, public_port, agent_url,
  reality_public_key, reality_short_id, reality_sni,
  max_users, is_active, sort_order
) VALUES (
  'fi1',
  'Exit #2 (srv1541843)',
  '51.250.112.128',
  2096,
  'https://51.250.112.128:8444',
  '<pbk entry>',
  '6ba85179e30d4fc2',
  'www.wikipedia.org',
  50,
  true,
  2
) ON CONFLICT (slug) DO NOTHING;
```

---

## 5. `.env` бота (Москва)

```env
# fallback для старых ключей без vpn_node_id
XRAY_PUBLIC_HOST=51.250.112.128
XRAY_PUBLIC_PORT=2053
XRAY_AGENT_URL=https://51.250.112.128:8443
REALITY_PUBLIC_KEY=<pbk entry>

BOT_PROXY_URL=http://user:pass@45.93.137.80:3128
```

Monitor опрашивает `agent_url` из `vpn_nodes` (entry agents, не exit).

---

## 6. Что **не** делать

| Ошибка | Почему |
|--------|--------|
| `public_host = IP exit` в `vpn_nodes` | Клиент пойдёт на зарубежный IP — режется LTE |
| xray-agent на exit для пользователей | UUID должны быть на **entry** inbound |
| Открыть 2087 exit на весь мир | Достаточно entry → exit |
| Менять pbk exit в VLESS-ссылке | В ссылке только pbk **entry** |

---

## 7. Платежи и чеки

См. migration 011: `payments.paid_at`, `receipt_fiscal_*`, `payment_webhook_events`. Админка: `/admin/payments`.
