# Россия — полная установка relay (порт 2053)

Сервер: **37.230.114.25**  
Литва уже настроена (admin + `bridge_russia` `9783d565-c328-479a-9f73-17fb90a5fdb2`).

Порт **443** занят `cv_portfolio_nginx` — **не трогать**. Xray на **2053**.

---

## Шаг 1. Подключиться

```bash
ssh root@37.230.114.25
```

---

## Шаг 2. Установить Xray

Скрипт `install-release.sh` с GitHub **часто не работает с российского сервера** (блокировка GitHub / таймаут curl). Варианты ниже.

### Вариант A — скрипт из репозитория (рекомендуется)

```bash
cd /opt/netagent
sudo apt install -y unzip curl    # или: yum install -y unzip curl

# без прокси
sudo sh scripts/install_xray_manual.sh

# если GitHub не открывается — через Squid на Литве (подставьте user:pass)
sudo HTTPS_PROXY=http://USER:PASS@45.93.137.80:3128 \
  sh scripts/install_xray_manual.sh
```

### Вариант B — вручную одной командой

```bash
sudo apt install -y unzip curl
VER=26.2.2
cd /tmp
curl -fL -O "https://github.com/XTLS/Xray-core/releases/download/v${VER}/Xray-linux-64.zip"
# с прокси: curl -x http://USER:PASS@45.93.137.80:3128 -fL -O ...
unzip -o Xray-linux-64.zip xray
sudo install -m 755 xray /usr/local/bin/xray
sudo mkdir -p /usr/local/etc/xray
xray version
```

Для **arm64** замените zip на `Xray-linux-arm64-v8a.zip`.

### Вариант C — скопировать с Литвы (если GitHub недоступен)

На **Литве** (там xray уже есть):

```bash
# с вашего ПК или с России
scp root@45.93.137.80:/usr/local/bin/xray /tmp/xray
scp /tmp/xray root@37.230.114.25:/usr/local/bin/xray
ssh root@37.230.114.25 "chmod 755 /usr/local/bin/xray && xray version"
```

### Вариант D — официальный install-script (если GitHub открыт)

```bash
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
```

Документация: [Project X — Install](https://xtls.github.io/en/document/install.html)

### systemd (если `status=216/GROUP` — группа `nobody` не существует)

```bash
sudo tee /etc/systemd/system/xray.service <<'EOF'
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
sudo systemctl daemon-reload
```

Порт 2053 — root допустим. Для 443 нужны capabilities или User=nobody + Group=nogroup.

Проверка:

```bash
which xray
xray version
```

---

## Шаг 3. Ключи России + UUID телефона

```bash
xray x25519
```

Пример вывода:

```
PrivateKey: aB3dEf9...длинная_строка
Password: xY7zQ2...ещё_строка
Hash32: ...
```

Запишите в блокнот:

| Название | Откуда | Куда вставить |
|----------|--------|----------------|
| **RUSSIA_PRIVATE_KEY** | строка `PrivateKey:` | inbound `realitySettings.privateKey` |
| **PBK_RUSSIA** | строка `Password:` (или `Public key:` если есть) | VLESS-ссылка, `.env` бота |

```bash
PHONE_UUID=$(xray uuid)
echo "PHONE_UUID=$PHONE_UUID"
```

Запишите **PHONE_UUID**.

---

## Шаг 4. Публичный ключ Литвы (PBK_LITHUANIA)

Если не сохранили при настройке Литвы — на **литовском** сервере:

```bash
ssh root@45.93.137.80
xray x25519 -i "eGdm5HgRgqJFCfq-SNUhbeRw35bqGCUd3l81X0xRS3g"
```

Строка **Public key:** (длинная base64url) → это **PBK_LITHUANIA**.

Вернитесь на Россию:

```bash
ssh root@37.230.114.25
```

---

## Шаг 5. Config Xray

```bash
sudo mkdir -p /usr/local/etc/xray
sudo cp /opt/netagent/configs/xray-russia-relay-2053.example.json \
  /usr/local/etc/xray/config.json
sudo nano /usr/local/etc/xray/config.json
```

### Что заменить (3 места)

| В файле найти | Вставить |
|---------------|----------|
| `REPLACE_USER_UUID` | ваш `PHONE_UUID` |
| `REPLACE_RUSSIA_PRIVATE_KEY` | `RUSSIA_PRIVATE_KEY` |
| `REPLACE_LITHUANIA_PUBLIC_KEY` | `PBK_LITHUANIA` |

### Что уже правильно — не менять

| Поле | Значение |
|------|----------|
| inbound `port` | `2053` |
| outbound `address` | `45.93.137.80` |
| outbound `port` | `443` |
| outbound user `id` | `9783d565-c328-479a-9f73-17fb90a5fdb2` |
| `shortIds` / `shortId` | `6ba85179e30d4fc2` |
| `dest` / `serverNames` / `serverName` | `www.wikipedia.org` |

### Что означает config

```
Телефон → inbound users-in (37.230.114.25:2053, ключи России)
         → routing
         → outbound to-lithuania (мост UUID + PBK Литвы)
         → 45.93.137.80:443
         → интернет
```

---

## Шаг 6. Проверка и запуск

```bash
sudo xray run -test -c /usr/local/etc/xray/config.json
```

Должно: `Configuration OK`.

```bash
sudo chmod 644 /usr/local/etc/xray/config.json
sudo systemctl enable xray
sudo systemctl restart xray
sudo systemctl status xray
```

---

## Шаг 7. Firewall

```bash
sudo ufw allow 2053/tcp
sudo ufw status
```

Проверка:

```bash
ss -lntp | grep -E '2053|443'
```

| Порт | Кто |
|------|-----|
| 443 | `docker-proxy` / `cv_portfolio_nginx` (сайт) |
| 2053 | `xray` |

---

## Шаг 8. VLESS-ссылка для iPhone

```bash
cd /opt/netagent
python scripts/build_relay_vless_link.py \
  --host 37.230.114.25 \
  --port 2053 \
  --uuid "PHONE_UUID" \
  --pbk "PBK_RUSSIA" \
  --sid 6ba85179e30d4fc2 \
  --name "NetAgent-RU"
```

Подставьте реальные `PHONE_UUID` и `PBK_RUSSIA` (без кавычек в uuid/pbk если нет пробелов).

Скопируйте вывод `vless://...` → Streisand → импорт.

В ссылке проверьте:
- host `37.230.114.25`
- port **2053**
- `pbk=` = **PBK_RUSSIA** (не Литвы)

---

## Шаг 9. Тест

1. iPhone: Wi‑Fi **выключить**, только LTE.
2. Streisand → NetAgent-RU → подключить.
3. Safari — сайты открываются.

Не работает:

```bash
journalctl -u xray -n 50 --no-pager
```

На Литве при подключении:

```bash
journalctl -u xray -n 30 --no-pager
```

---

## Шаг 10. Бот NetAgent (после успешного LTE)

```bash
cd /opt/netagent
nano .env
```

Изменить:

```env
XRAY_PUBLIC_HOST=37.230.114.25
XRAY_PUBLIC_PORT=2053
REALITY_PUBLIC_KEY=PBK_RUSSIA
REALITY_SHORT_ID=6ba85179e30d4fc2
REALITY_SNI=www.wikipedia.org
```

Очистить старые устройства (опционально):

```bash
docker compose exec postgres psql -U netagent -d netagent -c "DELETE FROM devices;"
```

```bash
docker compose up -d --build bot
```

Xray-agent остаётся на **Литве**. Мост `bridge_russia` не удалять.

---

---

## Типичные ошибки

| Симптом | Решение |
|---------|---------|
| `status=216/GROUP` | В unit файле `Group=nobody` не существует → `User=root` / `Group=root` |
| `publicKey` в outbound | **Public key** из `xray x25519 -i PRIVATE_KEY` на Литве, **не** privateKey |
| `run -test` failed | Проверить JSON и ключи |

## Чеклист

- [ ] `xray run -test` OK
- [ ] `ss` показывает xray на 2053
- [ ] `ufw` разрешает 2053
- [ ] Ссылка с `:2053` и PBK России
- [ ] LTE тест OK
- [ ] `.env` бота обновлён
