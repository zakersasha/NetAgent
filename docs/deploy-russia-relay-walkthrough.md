# Relay Россия → Литва — пошаговая установка

**BRIDGE_UUID:** `9783d565-c328-479a-9f73-17fb90a5fdb2`

| Сервер | IP | Роль |
|--------|-----|------|
| Литва | `45.93.137.80` | Выход в интернет (exit) |
| Россия | `37.230.114.25` | Вход для клиентов (LTE) |

Телефон → Россия:443 → Литва:443 → интернет.

---

## ЧАСТЬ A. Литва (`45.93.137.80`)

### A1. Остановить agent (чтобы не переписал config)

```bash
ssh root@45.93.137.80
sudo systemctl stop netagent-xray-agent
```

### A2. Бэкап и новый config

```bash
sudo cp /usr/local/etc/xray/config.json \
  /usr/local/etc/xray/config.json.bak.$(date +%F-%H%M)
```

Скопировать готовый config из репозитория **или** вставить вручную:

```bash
sudo nano /usr/local/etc/xray/config.json
```

**Что меняется по сравнению с вашим текущим config:**

| Было | Стало |
|------|--------|
| 3 clients (admin + 2 пользователя) | 2 clients: **admin** + **мост** |
| `7c4088bd-...` user_tg | **удалён** |
| `989e7ddf-...` phone | **удалён** |
| — | **добавлен** `9783d565-c328-479a-9f73-17fb90a5fdb2` email `bridge_russia` |
| `privateKey`, `shortIds`, Reality | **без изменений** |

Полный файл: `configs/xray-lithuania-exit.example.json` в репозитории.

### A3. Проверка и запуск Xray

```bash
sudo xray run -test -c /usr/local/etc/xray/config.json
sudo chmod 644 /usr/local/etc/xray/config.json
sudo systemctl restart xray
sudo systemctl status xray
ss -lntp | grep ':443'
```

Должно быть `Configuration OK` и xray слушает `443`.

### A4. Публичный ключ Литвы (нужен для России)

```bash
xray x25519 -i "eGdm5HgRgqJFCfq-SNUhbeRw35bqGCUd3l81X0xRS3g"
```

Сохраните строку **Public key** (длинная base64url) — это **PBK_LITHUANIA** для outbound на России.

Пример вывода:

```
PrivateKey: eGdm5HgRgqJFCfq-SNUhbeRw35bqGCUd3l81X0xRS3g
Password: ...
Public key: YTQ_dIa_739_...   ← это PBK_LITHUANIA
```

### A5. Agent — reserved для моста и admin

```bash
sudo nano /etc/netagent/xray-agent.env
```

Добавить/обновить:

```env
AGENT_RESERVED_EMAILS=admin@netagent.local,bridge_russia
AGENT_RESERVED_UUIDS=6f176e02-bae9-4998-8bb4-099cbb76981c,9783d565-c328-479a-9f73-17fb90a5fdb2
```

```bash
sudo systemctl start netagent-xray-agent
sudo systemctl status netagent-xray-agent
```

---

## ЧАСТЬ B. Россия (`37.230.114.25`)

### B1. Проверить порт 443

```bash
ssh root@37.230.114.25
ss -lntp | grep ':443'
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E '443|NAMES'
```

| Результат | Действие |
|-----------|----------|
| Пусто | inbound Xray на **443** → `configs/xray-russia-relay.example.json` |
| **nginx** на хосте | inbound на **2053** |
| **docker-proxy** на 443 | Не трогать контейнер (часто сайт). Xray на **2053** → `configs/xray-russia-relay-2053.example.json` |

Кто держит 443 в Docker:

```bash
docker ps -q | xargs -r docker inspect \
  --format '{{.Name}} {{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}} {{end}}' \
  | grep 443
```

### B2. Установить Xray (если ещё нет)

```bash
which xray || bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
xray version
```

### B3. Сгенерировать ключи России и UUID телефона

```bash
xray x25519
```

Запишите:

| Поле в выводе | Куда |
|---------------|------|
| **PrivateKey** | `REPLACE_RUSSIA_PRIVATE_KEY` в config inbound |
| **Password** или **Public key** | **PBK_RUSSIA** — для VLESS-ссылки на телефон |

```bash
PHONE_UUID=$(xray uuid)
echo "PHONE_UUID=$PHONE_UUID"
```

Сохраните **PHONE_UUID** и **PBK_RUSSIA**.

### B4. Config Xray на России

```bash
sudo mkdir -p /usr/local/etc/xray
sudo cp /opt/netagent/configs/xray-russia-relay.example.json \
  /usr/local/etc/xray/config.json
sudo nano /usr/local/etc/xray/config.json
```

**Заменить в файле:**

| Плейсхолдер | Значение |
|-------------|----------|
| `REPLACE_USER_UUID` | `PHONE_UUID` из B3 |
| `REPLACE_RUSSIA_PRIVATE_KEY` | PrivateKey из `xray x25519` (Россия) |
| `REPLACE_BRIDGE_UUID` | `9783d565-c328-479a-9f73-17fb90a5fdb2` (уже в шаблоне) |
| `REPLACE_LITHUANIA_PUBLIC_KEY` | **PBK_LITHUANIA** из шага A4 |

**Что делает config:**

| Блок | Назначение |
|------|------------|
| inbound `users-in` :443 | Клиенты подключаются сюда (ваш телефон) |
| outbound `to-lithuania` | Xray на России идёт на Литву как клиент с BRIDGE_UUID |
| routing | Весь трафик users-in → to-lithuania |

### B5. Порт 443 или 2053

Если nginx занял 443, в inbound измените:

```json
"port": 2053
```

и в ссылке для телефона `--port 2053`, `ufw allow 2053/tcp`.

### B6. Запуск

```bash
sudo xray run -test -c /usr/local/etc/xray/config.json
sudo chmod 644 /usr/local/etc/xray/config.json
sudo systemctl enable xray
sudo systemctl restart xray
sudo systemctl status xray

sudo ufw allow 443/tcp
# или: sudo ufw allow 2053/tcp
```

### B7. VLESS-ссылка для iPhone

```bash
cd /opt/netagent
python scripts/build_relay_vless_link.py \
  --host 37.230.114.25 \
  --port 443 \
  --uuid "$PHONE_UUID" \
  --pbk "PBK_RUSSIA" \
  --sid 6ba85179e30d4fc2 \
  --name "NetAgent-RU"
```

Скопируйте `vless://...` → Streisand → импорт.

**Не используйте** старую ссылку с `45.93.137.80` и старым pbk Литвы для LTE.

---

## ЧАСТЬ C. Тест на iPhone

1. Wi‑Fi **выключить**, только LTE.
2. Streisand → подключить **NetAgent-RU**.
3. Открыть сайт в Safari.

Если ок — relay работает.

4. Wi‑Fi включить — тоже должно работать.

**Админ с Литвой напрямую (Wi‑Fi):** отдельная ссылка с host `45.93.137.80`, uuid `6f176e02-...`, pbk **Литвы** — только для вас, не для продажи.

---

## ЧАСТЬ D. Бот NetAgent (после успешного LTE-теста)

На России:

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

```bash
docker compose up -d --build bot
```

Очистить старые устройства в БД (опционально):

```bash
docker compose exec postgres psql -U netagent -d netagent -c "DELETE FROM devices;"
```

Новые ключи в боте будут с **российским** host и pbk.

Xray-agent на **Литве** не переносим — он добавляет клиентов в exit config. Мост `bridge_russia` не удалять.

---

## ЧАСТЬ E. Если не работает

```bash
# Россия
journalctl -u xray -n 80 --no-pager

# Литва
journalctl -u xray -n 80 --no-pager
```

| Проблема | Решение |
|----------|---------|
| `run -test` failed | JSON/ключи — проверить запятые и плейсхолдеры |
| LTE timeout | Порт 2053, Fragment в Streisand |
| Россия ok, нет интернета | PBK_LITHUANIA или BRIDGE_UUID неверный на outbound |
| agent удалил мост | Проверить AGENT_RESERVED_* на Литве |

---

## Сводка «что на что»

```
Телефон (LTE)
  vless://PHONE_UUID@37.230.114.25:443?pbk=PBK_RUSSIA&...
       ↓
Россия inbound (users-in) — PrivateKey России
       ↓ routing
Россия outbound (to-lithuania) — uuid=9783d565-..., pbk=PBK_LITHUANIA
       ↓
Литва inbound — client bridge_russia
       ↓ freedom
Интернет
```

Старые пользователи `7c4088bd-...` и `989e7ddf-...` на Литве **удалены** — их ссылки не работают. Новые — только через Россию.
