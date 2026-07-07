# Вторая VPN-нода за рубежом

Распределение нагрузки: новые пользователи автоматически попадают на ноду с **наименьшим числом активных ключей** (лимит `max_users` на ноду, по умолчанию 50).

| Нода | Роль | Порт VPN | Agent |
|------|------|----------|-------|
| `lt1` | Литва #1 (существующая) | **443** | `8443` |
| `fi1` | Новая нода (пример) | **2087** | `8443` |

Прокси для Telegram/OpenAI (`45.93.137.80:3128`) **не трогаем** — он остаётся на литовском сервере.

---

## 1. Подготовка нового сервера (например `NEW_IP`)

Требования: Ubuntu 22.04+, открыты порты **2087/tcp** (VPN) и **8443/tcp** только с `37.230.114.25`.

### 1.1 Xray

```bash
ssh root@NEW_IP

apt update && apt install -y unzip curl
curl -fL -o /tmp/xray.zip \
  https://github.com/XTLS/Xray-core/releases/download/v26.2.2/Xray-linux-64.zip
unzip -o /tmp/xray.zip xray -d /tmp
install -m 755 /tmp/xray /usr/local/bin/xray
mkdir -p /usr/local/etc/xray
```

Сгенерируйте **новые** Reality-ключи (отдельно от литовской ноды):

```bash
xray x25519
# PrivateKey → в config.json
# Password (public) → REALITY_PUBLIC_KEY / pbk в ссылках
```

Short ID:

```bash
openssl rand -hex 8
```

### 1.2 config.json (порт **2087**)

```bash
nano /usr/local/etc/xray/config.json
```

Минимальный шаблон:

```json
{
  "log": { "loglevel": "warning" },
  "stats": {},
  "api": {
    "tag": "api",
    "services": ["StatsService"]
  },
  "policy": {
    "levels": {
      "0": { "statsUserUplink": true, "statsUserDownlink": true }
    },
    "system": { "statsInboundUplink": true, "statsInboundDownlink": true }
  },
  "inbounds": [
    {
      "tag": "vless-reality-in",
      "port": 2087,
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
          "privateKey": "ВАШ_PRIVATE_KEY",
          "shortIds": ["ваш_short_id_16hex"]
        }
      },
      "sniffing": { "enabled": true, "destOverride": ["http", "tls"] }
    },
    {
      "listen": "127.0.0.1",
      "port": 10085,
      "protocol": "dokodemo-door",
      "settings": { "address": "127.0.0.1" },
      "tag": "api"
    }
  ],
  "outbounds": [{ "protocol": "freedom", "tag": "direct" }],
  "routing": {
    "rules": [{ "type": "field", "inboundTag": ["api"], "outboundTag": "api" }]
  }
}
```

```bash
xray run -test -c /usr/local/etc/xray/config.json
systemctl enable --now xray
ss -lntp | grep 2087
ufw allow 2087/tcp
```

---

## 2. xray-agent на новой ноде

Повторите [deploy-lithuania.md](deploy-lithuania.md) на `NEW_IP`:

```bash
cd /opt && git clone <repo> netagent && cd netagent
python3 -m venv .venv && .venv/bin/pip install -e .

openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/netagent/certs/agent.key \
  -out /etc/netagent/certs/agent.crt -days 3650 -subj "/CN=NEW_IP"
```

`/etc/netagent/xray-agent.env`:

```env
XRAY_CONFIG_PATH=/usr/local/etc/xray/config.json
XRAY_INBOUND_TAG=vless-reality-in
XRAY_MAX_USERS=50
XRAY_RELOAD_CMD=systemctl restart xray
XRAY_PUBLIC_HOST=NEW_IP

AGENT_API_KEY=<тот же или новый ключ — пропишите в .env Москвы>
AGENT_ALLOWED_IPS=37.230.114.25
AGENT_PORT=8443

REALITY_PUBLIC_KEY=<pbk из xray x25519>
REALITY_SHORT_ID=<16 hex>
REALITY_SNI=www.wikipedia.org
```

Firewall:

```bash
ufw allow from 37.230.114.25 to any port 8443 proto tcp
ufw deny 8443/tcp
systemctl enable --now netagent-xray-agent
```

Проверка **с московского сервера**:

```bash
export XRAY_AGENT_URL=https://NEW_IP:8443
export XRAY_AGENT_API_KEY=<key>
python scripts/xray_cli.py health
```

---

## 3. Миграция БД (Москва)

```bash
cd /opt/netagent
docker compose exec bot alembic upgrade head
```

Добавьте ноду в Postgres:

```sql
INSERT INTO vpn_nodes (
  slug, name, public_host, public_port, agent_url,
  reality_public_key, reality_short_id, reality_sni,
  max_users, is_active, sort_order
) VALUES (
  'fi1',
  'Финляндия #1',
  'NEW_IP',
  2087,
  'https://NEW_IP:8443',
  'ВАШ_REALITY_PUBLIC_KEY',
  'ваш_short_id',
  'www.wikipedia.org',
  50,
  true,
  2
);
```

---

## 4. Московский `.env`

```env
XRAY_PUBLIC_HOST=45.93.137.80
XRAY_PUBLIC_PORT=443
XRAY_AGENT_URL=https://45.93.137.80:8443

BOT_PROXY_URL=http://user:pass@45.93.137.80:3128
```

Перезапуск:

```bash
docker compose up -d --build
```

---

## 5. Балансировка

1. Новый профиль → нода с минимумом активных ключей.
2. Нода с `active >= max_users` пропускается.
3. `devices.vpn_node_id` фиксирует привязку.
4. Monitor опрашивает все ноды из `vpn_nodes`.

Старые ключи без `vpn_node_id` работают через `XRAY_PUBLIC_*` из `.env`.

---

## 6. Платежи и чеки

| Поле | Назначение |
|------|------------|
| `payments.external_id` | ID ЮKassa |
| `payments.paid_at` | время оплаты |
| `payments.receipt_fiscal_*` | чек 54-ФЗ |
| `payments.provider_payload` | полный JSON |
| `payment_webhook_events` | все webhook (audit) |

Админка: `/admin/payments`.

```sql
SELECT id, amount, external_id, paid_at, payment_method_title,
       receipt_fiscal_document_number
FROM payments WHERE status = 'succeeded' ORDER BY paid_at DESC;
```
