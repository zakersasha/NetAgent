# Контроль устройств через Xray Stats API

> Полная инструкция: варианты anti-sharing, relay, деплой agent и поток бота — **[key-enforcement-guide.md](key-enforcement-guide.md)**.

## Модель

1. Пользователь добавляет устройство в боте → генерируются:
   - `uuid` — ключ в Xray (VLESS)
   - `device_id` — `sha256(user_id:slug:uuid)` для учёта в БД
   - `xray_email` — `{telegram_id}_{suffix}` (нужен для Stats API)

2. В Postgres (`devices`):
   - `device_id`, `uuid`, `device_name`, `status`
   - `last_ip`, `last_seen` — обновляет **monitor**
   - `suspended_at`, `suspended_reason` — при автоблоке

3. Сервис **monitor** (Россия, Docker) каждые 30 сек:
   - `GET https://45.93.137.80:8443/stats/users_online` (через xray-agent)
   - сравнивает online IP по `xray_email`
   - обновляет `last_ip` / `last_seen`
   - при нарушении → `remove_user` в Xray + `status=suspended` в БД

## Правила блокировки

| Условие | Действие |
|---------|----------|
| Больше 1 online IP на один UUID/email | suspend |
| Online IP из разных стран (RU + DE + TR…) | suspend |

Проверка стран требует GeoLite2:

```bash
# на сервере России
sudo mkdir -p /opt/netagent/geoip
# скачать GeoLite2-Country.mmdb с maxmind.com → /opt/netagent/geoip/GeoLite2-Country.mmdb
```

В `.env`:

```env
GEOIP_DATABASE_PATH=/opt/netagent/geoip/GeoLite2-Country.mmdb
DEVICE_MONITOR_INTERVAL_SECONDS=30
DEVICE_MONITOR_MAX_ONLINE_IPS=1
```

Без GeoIP файла работает только правило «несколько IP» (достаточно для «ключ с телефона и с ПК»).

## Настройка Xray на Литве (обязательно)

В `/usr/local/etc/xray/config.json`:

```json
{
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
    }
  },
  "inbounds": [
    {
      "tag": "api",
      "listen": "127.0.0.1",
      "port": 10085,
      "protocol": "dokodemo-door",
      "settings": { "address": "127.0.0.1" }
    },
    {
      "tag": "vless-reality-in",
      "protocol": "vless",
      "settings": {
        "clients": [
          { "id": "...", "email": "544709692_phone", "flow": "xtls-rprx-vision" }
        ]
      }
    }
  ]
}
```

В `xray-agent.env`:

```env
XRAY_API_SERVER=127.0.0.1:10085
XRAY_BIN=/usr/local/bin/xray
```

Проверка на Литве:

```bash
xray api statsonlineiplist -server=127.0.0.1:10085 -email "544709692_phone"
xray api statsonlineiplist -server=127.0.0.1:10085 -all
```

## После suspend

Ключ перестаёт работать. В боте устройство скрыто из списка (status ≠ active).
Пользователь удаляет «мертвое» устройство (если осталось в UI) и добавляет заново — новый UUID.

## Запуск

```bash
docker compose up -d --build   # postgres + bot + monitor
docker compose logs -f monitor
```
