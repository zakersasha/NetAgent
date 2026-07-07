# Relay: Яндекс entry + exit #2 (`92.242.187.168`)

Полный гайд: что делать на **иностранной ноде** и на **Яндекс-машине**.

## Схема

```
Телефон (LTE)
    │
    ├─ vless @51.250.112.128:2053  (пул lt1) ──► 45.93.137.80:443  (Литва)
    │
    └─ vless @51.250.112.128:2096  (пул fi1) ──► 92.242.187.168:2087 (exit #2)
```

| Сервер | IP | Роль |
|--------|-----|------|
| Entry (Яндекс) | `51.250.112.128` | Клиенты подключаются сюда, xray-agent |
| Exit #1 (Литва) | `45.93.137.80:443` | Уже настроен, мост `9783d565-…` |
| Exit #2 | `92.242.187.168:2087` | Новая нода, только мост + выход |
| App (бот) | `37.230.114.25` | Postgres, bot, monitor |

**В VLESS-ссылках пользователей — только IP Яндекса и Reality-ключи entry, не `92.242.187.168`.**

---

# ЧАСТЬ A. Exit #2 — `root@srv1541843` (`92.242.187.168`)

Xray у вас уже запущен на **2087**. Дальше — довести до relay-exit.

## A1. Бэкап

```bash
ssh root@92.242.187.168

cp /usr/local/etc/xray/config.json \
  /usr/local/etc/xray/config.json.bak.$(date +%F-%H%M)
```

## A2. UUID моста (сохраните — нужен на Яндексе)

```bash
BRIDGE2=$(xray uuid)
echo "BRIDGE2=$BRIDGE2"
```

Запишите `BRIDGE2` в блокнот (один и тот же UUID на exit и в outbound entry).

## A3. Полный `config.json` на exit

Reality exit #2 (уже сгенерированы у вас):

| Параметр | Значение |
|----------|----------|
| PrivateKey | `AB3hjI-FdE0z3CFyqJhfr8MJvpVprz2AunP8u-zjO0g` |
| PublicKey (pbk) | `WDqt_crB3vWrle5JQ4DmUm2PHuXTR9nhicu0jv3ySSY` |
| shortId | `56f8dc4a36e55951` |

```bash
nano /usr/local/etc/xray/config.json
```

Вставьте (подставьте `BRIDGE2` из A2):

```json
{
  "log": { "loglevel": "warning" },
  "inbounds": [
    {
      "tag": "vless-reality-in",
      "listen": "0.0.0.0",
      "port": 2087,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "BRIDGE2_UUID_СЮДА",
            "flow": "xtls-rprx-vision",
            "email": "bridge_russia_2"
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
          "privateKey": "AB3hjI-FdE0z3CFyqJhfr8MJvpVprz2AunP8u-zjO0g",
          "shortIds": ["56f8dc4a36e55951"]
        }
      },
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      }
    }
  ],
  "outbounds": [
    { "protocol": "freedom", "tag": "direct" }
  ],
  "routing": {
    "rules": []
  }
}
```

> На exit **нет пользовательских UUID** — только `bridge_russia_2`.  
> Порт **443** (Docker Amnezia) не трогаем.

Опционально: добавьте свой admin-UUID в `clients` (для прямого теста exit по Wi‑Fi).

## A4. Проверка и перезапуск

```bash
xray run -test -c /usr/local/etc/xray/config.json
chmod 644 /usr/local/etc/xray/config.json
systemctl restart xray
systemctl status xray
ss -lntp | grep 2087
curl -4 ifconfig.me
```

Должно быть: `Configuration OK`, xray на `2087`, IP = `92.242.187.168`.

## A5. Firewall (2087 только с entry)

```bash
ufw allow from 51.250.112.128 to any port 2087 proto tcp
ufw deny 2087/tcp
ufw status
```

**xray-agent на exit для пользователей не ставим** — провизионирование только на Яндексе.

## A6. Чеклист exit #2

- [ ] `BRIDGE2` записан
- [ ] В config только мост (+ admin опционально)
- [ ] `xray run -test` → OK
- [ ] 2087 открыт **только** для `51.250.112.128`

---

# ЧАСТЬ B. Entry — Яндекс `51.250.112.128`

Сейчас работает один путь: `users-in:2053` → Литва. Добавляем второй пул `fi1`.

## B1. Бэкап

```bash
ssh root@51.250.112.128

cp /usr/local/etc/xray/config.json \
  /usr/local/etc/xray/config.json.bak.$(date +%F-%H%M)
```

## B2. Публичный ключ entry (для VLESS-ссылок и agent)

```bash
xray x25519 -i "iO1Mp_gBlUhSr2F6lEyIrHZ5dZNe39CxPifIk0V_o0k"
```

Строка **Password** или **Public key** → это **PBK_ENTRY**. Сохраните.

Entry Reality (из текущего config):

| Параметр | Значение |
|----------|----------|
| privateKey | `iO1Mp_gBlUhSr2F6lEyIrHZ5dZNe39CxPifIk0V_o0k` |
| shortId | `6ba85179e30d4fc2` |
| sni | `www.wikipedia.org` |

## B3. Обновить `config.json` на entry

Откройте config и **сохраните существующих clients** в `users-in` (не удаляйте текущих пользователей).

Добавьте:

1. **Второй inbound** `users-in-fi1` на порту **2096**
2. **Outbound** `to-fi1` → `92.242.187.168:2087`
3. **Routing** — два правила

Фрагменты для вставки:

### Inbound fi1 (новый)

```json
{
  "tag": "users-in-fi1",
  "listen": "0.0.0.0",
  "port": 2096,
  "protocol": "vless",
  "settings": {
    "clients": [],
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
      "privateKey": "iO1Mp_gBlUhSr2F6lEyIrHZ5dZNe39CxPifIk0V_o0k",
      "shortIds": ["6ba85179e30d4fc2"]
    }
  },
  "sniffing": {
    "enabled": true,
    "destOverride": ["http", "tls", "quic"]
  }
}
```

### Outbound to-fi1 (новый)

Подставьте `BRIDGE2` из части A:

```json
{
  "tag": "to-fi1",
  "protocol": "vless",
  "settings": {
    "vnext": [
      {
        "address": "92.242.187.168",
        "port": 2087,
        "users": [
          {
            "id": "BRIDGE2_UUID_СЮДА",
            "encryption": "none",
            "flow": "xtls-rprx-vision",
            "email": "bridge_russia_2"
          }
        ]
      }
    ]
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

### Routing (заменить rules)

```json
"routing": {
  "domainStrategy": "AsIs",
  "rules": [
    {
      "type": "field",
      "inboundTag": ["users-in"],
      "outboundTag": "to-lithuania"
    },
    {
      "type": "field",
      "inboundTag": ["users-in-fi1"],
      "outboundTag": "to-fi1"
    }
  ]
}
```

Outbound `to-lithuania` **не меняем** (address `45.93.137.80`, bridge `9783d565-c328-479a-9f73-17fb90a5fdb2`).

### Stats API (если ещё нет — нужен для monitor)

В корень config:

```json
"stats": {},
"api": {
  "tag": "api",
  "services": ["StatsService"]
},
"policy": {
  "levels": {
    "0": {
      "statsUserUplink": true,
      "statsUserDownlink": true,
      "statsUserOnline": true
    }
  },
  "system": {
    "statsInboundUplink": true,
    "statsInboundDownlink": true
  }
}
```

Inbound API (если ещё нет):

```json
{
  "listen": "127.0.0.1",
  "port": 10085,
  "protocol": "dokodemo-door",
  "settings": { "address": "127.0.0.1" },
  "tag": "api"
}
```

И правило routing:

```json
{ "type": "field", "inboundTag": ["api"], "outboundTag": "api" }
```

(outbound `"tag": "api"` — blackhole или dokodemo; см. [device-enforcement.md](device-enforcement.md))

## B4. Проверка Xray на entry

```bash
xray run -test -c /usr/local/etc/xray/config.json
chmod 644 /usr/local/etc/xray/config.json
systemctl restart xray
systemctl status xray
ss -lntp | grep -E '2053|2096'
```

## B5. Firewall entry

```bash
ufw allow 2053/tcp
ufw allow 2096/tcp
ufw status
```

---

# ЧАСТЬ C. xray-agent на Яндексе (два instance)

| Пул | Порт agent | Inbound tag | Порт в VLESS |
|-----|------------|-------------|--------------|
| lt1 | `8443` | `users-in` | `2053` |
| fi1 | `8444` | `users-in-fi1` | `2096` |

Agent #1 (lt1) — если уже есть, проверьте env. Agent #2 (fi1) — новый.

## C1. Agent fi1 — env

```bash
mkdir -p /etc/netagent/certs

# Сертификат (если на lt1 уже есть — можно те же файлы)
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/netagent/certs/agent-fi1.key \
  -out /etc/netagent/certs/agent-fi1.crt \
  -days 3650 -subj "/CN=51.250.112.128"

nano /etc/netagent/xray-agent-fi1.env
```

```env
XRAY_CONFIG_PATH=/usr/local/etc/xray/config.json
XRAY_INBOUND_TAG=users-in-fi1
XRAY_MAX_USERS=50
XRAY_RELOAD_CMD=systemctl restart xray
XRAY_PUBLIC_HOST=51.250.112.128
XRAY_PUBLIC_PORT=2096

AGENT_API_KEY=<тот же ключ что на lt1 agent, или новый — тогда пропишите в Postgres>
AGENT_ALLOWED_IPS=37.230.114.25
AGENT_PORT=8444

REALITY_PUBLIC_KEY=<PBK_ENTRY из B2>
REALITY_SHORT_ID=6ba85179e30d4fc2
REALITY_SNI=www.wikipedia.org

XRAY_API_SERVER=127.0.0.1:10085
XRAY_BIN=/usr/local/bin/xray
```

## C2. Agent fi1 — systemd

```bash
nano /etc/systemd/system/netagent-xray-agent-fi1.service
```

```ini
[Unit]
Description=NetAgent Xray Agent (fi1 pool)
After=network.target xray.service

[Service]
Type=simple
WorkingDirectory=/opt/netagent
EnvironmentFile=/etc/netagent/xray-agent-fi1.env
ExecStart=/opt/netagent/.venv/bin/python -m uvicorn xray_agent.app:app \
  --host 0.0.0.0 \
  --port 8444 \
  --ssl-keyfile /etc/netagent/certs/agent-fi1.key \
  --ssl-certfile /etc/netagent/certs/agent-fi1.crt
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable netagent-xray-agent-fi1
systemctl start netagent-xray-agent-fi1
systemctl status netagent-xray-agent-fi1
```

## C3. Firewall agents

```bash
ufw allow from 37.230.114.25 to any port 8443 proto tcp
ufw allow from 37.230.114.25 to any port 8444 proto tcp
ufw deny 8443/tcp
ufw deny 8444/tcp
```

## C4. Проверка agent с Москвы

```bash
ssh root@37.230.114.25

export KEY=<AGENT_API_KEY>

curl -k -H "X-API-Key: $KEY" https://51.250.112.128:8443/health
curl -k -H "X-API-Key: $KEY" https://51.250.112.128:8444/health
```

Оба должны вернуть OK.

---

# ЧАСТЬ D. App-сервер Москва (`37.230.114.25`)

## D1. Миграция БД (если ещё не делали)

```bash
cd /opt/netagent
docker compose exec bot alembic upgrade head
```

## D2. Записи `vpn_nodes`

```bash
docker compose exec postgres psql -U netagent -d netagent
```

```sql
-- lt1: entry Яндекс, не Литва
UPDATE vpn_nodes SET
  public_host = '51.250.112.128',
  public_port = 2053,
  agent_url = 'https://51.250.112.128:8443',
  reality_public_key = 'PBK_ENTRY',
  reality_short_id = '6ba85179e30d4fc2',
  reality_sni = 'www.wikipedia.org'
WHERE slug = 'lt1';

INSERT INTO vpn_nodes (
  slug, name, public_host, public_port, agent_url,
  reality_public_key, reality_short_id, reality_sni,
  max_users, is_active, sort_order
) VALUES (
  'fi1',
  'Exit #2 (92.242.187.168)',
  '51.250.112.128',
  2096,
  'https://51.250.112.128:8444',
  'PBK_ENTRY',
  '6ba85179e30d4fc2',
  'www.wikipedia.org',
  50,
  true,
  2
) ON CONFLICT (slug) DO UPDATE SET
  public_host = EXCLUDED.public_host,
  public_port = EXCLUDED.public_port,
  agent_url = EXCLUDED.agent_url,
  reality_public_key = EXCLUDED.reality_public_key,
  reality_short_id = EXCLUDED.reality_short_id;
```

Замените `PBK_ENTRY` на значение из шага B2.

## D3. `.env` бота (fallback для старых ключей)

```env
XRAY_PUBLIC_HOST=51.250.112.128
XRAY_PUBLIC_PORT=2053
XRAY_AGENT_URL=https://51.250.112.128:8443
XRAY_AGENT_API_KEY=<ключ>
XRAY_AGENT_VERIFY_SSL=false
REALITY_PUBLIC_KEY=<PBK_ENTRY>
REALITY_SHORT_ID=6ba85179e30d4fc2
REALITY_SNI=www.wikipedia.org
```

```bash
docker compose up -d --build bot monitor
```

---

# ЧАСТЬ E. Тест end-to-end

## E1. Тест fi1 вручную (до бота)

На Яндексе добавьте тестового клиента в `users-in-fi1`:

```bash
TEST_UUID=$(xray uuid)
echo $TEST_UUID
```

Вставьте в `clients` inbound `users-in-fi1`, перезапустите xray.

VLESS-ссылка (подставьте UUID и PBK_ENTRY):

```
vless://TEST_UUID@51.250.112.128:2096?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.wikipedia.org&fp=chrome&pbk=PBK_ENTRY&sid=6ba85179e30d4fc2&type=tcp#NetAgent-fi1-test
```

iPhone: Wi‑Fi выкл, LTE → Streisand → импорт → подключить → Safari.

## E2. Тест через бота

1. Новая оплата / новый ключ в боте.
2. Проверить, что в ссылке `51.250.112.128` и порт `2053` или `2096` (не `92.242.187.168`).
3. LTE-тест.

## E3. Логи при проблемах

```bash
# Entry
journalctl -u xray -n 80 --no-pager
journalctl -u netagent-xray-agent-fi1 -n 50 --no-pager

# Exit #2
journalctl -u xray -n 80 --no-pager
```

| Симптом | Причина |
|---------|---------|
| Timeout на 2096 | ufw / порт не слушает |
| Подключился, нет интернета | неверный BRIDGE2 или pbk exit в outbound |
| Бот выдал ключ, не работает | UUID не в нужном inbound (2053 vs 2096) |

---

# Сводка «что где»

```
┌─────────────────────────────────────────────────────────────┐
│ 92.242.187.168 (exit #2)                                    │
│  • xray :2087 — только bridge_russia_2                      │
│  • firewall: 2087 ← 51.250.112.128 only                     │
│  • NO user agent                                             │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ VLESS Reality (bridge)
                              │
┌─────────────────────────────────────────────────────────────┐
│ 51.250.112.128 (entry Яндекс)                               │
│  • users-in :2053  → to-lithuania → 45.93.137.80:443         │
│  • users-in-fi1 :2096 → to-fi1 → 92.242.187.168:2087         │
│  • agent :8443 (lt1), :8444 (fi1)                           │
│  • Stats API :10085                                          │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ VLESS Reality (PBK_ENTRY)
                              │
                        Телефон клиента
```
