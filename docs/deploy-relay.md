# Relay: Россия → Литва (Wi‑Fi + LTE)

| Сервер | IP | Файл config |
|--------|-----|-------------|
| Литва (exit) | `45.93.137.80` | `configs/lithuania.json` |
| Россия (entry) | `51.250.112.128` | `configs/russia-relay.json` |

Схема: телефон → **51.250.112.128:2053** → **45.93.137.80:443** → интернет.

Порядок: **сначала Литва**, потом Россия.

---

## A. Литва `45.93.137.80`

### A1. Установка Xray (если ещё нет)

```bash
ssh root@45.93.137.80

apt update
apt install -y unzip curl

curl -fL -o /tmp/xray.zip \
  https://github.com/XTLS/Xray-core/releases/download/v26.2.2/Xray-linux-64.zip
unzip -o /tmp/xray.zip xray -d /tmp
install -m 755 /tmp/xray /usr/local/bin/xray
mkdir -p /usr/local/etc/xray
xray version
```

### A2. systemd

```bash
cat >/etc/systemd/system/xray.service <<'EOF'
[Unit]
Description=Xray Service
After=network.target

[Service]
User=root
Group=root
ExecStart=/usr/local/bin/xray run -config /usr/local/etc/xray/config.json
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
```

### A3. config.json

Скопируйте содержимое `configs/lithuania.json` из репозитория на ПК **или** целиком:

```bash
nano /usr/local/etc/xray/config.json
```

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
            "id": "6f176e02-bae9-4998-8bb4-099cbb76981c",
            "flow": "xtls-rprx-vision",
            "email": "admin@netagent.local"
          },
          {
            "id": "7c4088bd-eb58-501d-810f-accefebde006",
            "flow": "xtls-rprx-vision",
            "email": "user_tg_544709692@netagent.local"
          },
          {
            "id": "989e7ddf-acc4-4178-99d5-c3b4ea33a613",
            "flow": "xtls-rprx-vision",
            "email": "544709692_phone"
          },
          {
            "id": "9783d565-c328-479a-9f73-17fb90a5fdb2",
            "flow": "xtls-rprx-vision",
            "email": "bridge_russia"
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
          "privateKey": "eGdm5HgRgqJFCfq-SNUhbeRw35bqGCUd3l81X0xRS3g",
          "shortIds": ["6ba85179e30d4fc2"]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "tag": "direct"
    }
  ]
}
```

### A4. Запуск

```bash
xray run -test -c /usr/local/etc/xray/config.json
systemctl enable --now xray
systemctl status xray
ss -lntp | grep ':443'
```

Если xray-agent уже стоит — перед A3:

```bash
systemctl stop netagent-xray-agent
```

После запуска xray — agent снова:

```bash
systemctl start netagent-xray-agent
```

---

## B. Россия `51.250.112.128`

### B1. Установка Xray

```bash
ssh root@51.250.112.128

apt update
apt install -y unzip curl

curl -fL -o /tmp/xray.zip \
  https://github.com/XTLS/Xray-core/releases/download/v26.2.2/Xray-linux-64.zip
unzip -o /tmp/xray.zip xray -d /tmp
install -m 755 /tmp/xray /usr/local/bin/xray
mkdir -p /usr/local/etc/xray
xray version
```

Если GitHub не открывается — с ПК:

```bash
scp root@45.93.137.80:/usr/local/bin/xray /tmp/xray
scp /tmp/xray root@51.250.112.128:/usr/local/bin/xray
ssh root@51.250.112.128 "chmod 755 /usr/local/bin/xray"
```

### B2. systemd

```bash
cat >/etc/systemd/system/xray.service <<'EOF'
[Unit]
Description=Xray Service
After=network.target

[Service]
User=root
Group=root
ExecStart=/usr/local/bin/xray run -config /usr/local/etc/xray/config.json
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
```

### B3. config.json

`configs/russia-relay.json` **или**:

```bash
nano /usr/local/etc/xray/config.json
```

```json
{
  "log": { "loglevel": "info" },
  "inbounds": [
    {
      "tag": "users-in",
      "listen": "0.0.0.0",
      "port": 2053,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "989e7ddf-acc4-4178-99d5-c3b4ea33a613",
            "flow": "xtls-rprx-vision",
            "email": "544709692_phone"
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
          "privateKey": "iO1Mp_gBlUhSr2F6lEyIrHZ5dZNe39CxPifIk0V_o0k",
          "shortIds": ["6ba85179e30d4fc2"]
        }
      },
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls", "quic"]
      }
    }
  ],
  "outbounds": [
    {
      "tag": "to-lithuania",
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "45.93.137.80",
            "port": 443,
            "users": [
              {
                "id": "9783d565-c328-479a-9f73-17fb90a5fdb2",
                "encryption": "none",
                "flow": "xtls-rprx-vision",
                "email": "bridge_russia"
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
          "publicKey": "YTQ_dIa_739_d6x7OUAs2XjMbpX6UOnWBMkGVtEhi18",
          "shortId": "6ba85179e30d4fc2",
          "fingerprint": "chrome"
        }
      }
    },
    {
      "tag": "direct",
      "protocol": "freedom"
    }
  ],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {
        "type": "field",
        "inboundTag": ["users-in"],
        "outboundTag": "to-lithuania"
      }
    ]
  }
}
```

### B4. Запуск

```bash
xray run -test -c /usr/local/etc/xray/config.json
systemctl enable --now xray
systemctl status xray
ss -lntp | grep ':2053'
ufw allow 2053/tcp
```

Проверка relay с самой России:

```bash
curl -4 --max-time 5 https://ifconfig.me
```

Должен открываться интернет с сервера. Логи:

```bash
journalctl -u xray -n 30 --no-pager
```

---

## C. Ссылка для телефона (Wi‑Fi + LTE)

Импорт в Streisand / v2rayTun / Happ. **pbk — Россия**, не Литва.

```
vless://989e7ddf-acc4-4178-99d5-c3b4ea33a613@51.250.112.128:2053?encryption=none&type=tcp&security=reality&pbk=j-iuguAzBEJ4-u76nVncqDxBipKnsPgGkBOunpoYBXA&flow=xtls-rprx-vision&sni=www.wikipedia.org&fp=chrome&sid=6ba85179e30d4fc2#NetAgent
```

Проверка: LTE и Wi‑Fi → ifconfig.me → **45.93.137.80**.

Резерв Wi‑Fi direct (без relay):

```
vless://989e7ddf-acc4-4178-99d5-c3b4ea33a613@45.93.137.80:443?encryption=none&type=tcp&security=reality&pbk=YTQ_dIa_739_d6x7OUAs2XjMbpX6UOnWBMkGVtEhi18&flow=xtls-rprx-vision&sni=www.wikipedia.org&fp=chrome&sid=6ba85179e30d4fc2#LT-WiFi
```

---

## D. iPhone не коннектит

- Режим **Global**, DNS **Remote** / через VPN.
- Fingerprint: **ios** или **safari** вместо chrome.
- Fragment: ON (length 100–200).
- Логи на России: `journalctl -u xray -f`

## E. LTE не работает на 2053

Поменять в `russia-relay.json` поле `"port": 2053` → `443`, перезапуск xray, в ссылке порт **443**. На `51.250.112.128` проверьте, что 443 свободен: `ss -lntp | grep ':443'`.

## F. Новые ключи на России

Если на `51.250.112.128` нужны свои ключи:

```bash
xray x25519
```

- **PrivateKey** → `privateKey` в inbound России
- **Password** → `pbk` в VLESS-ссылке

Литва outbound `publicKey` не меняется (`YTQ_dIa_...`).
