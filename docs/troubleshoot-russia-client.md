# Диагностика: inbound OK, клиенты с iPhone не работают

## Сервер работает

`test_russia_inbound_local.sh` → `37.230.114.25` — inbound Reality на сервере **корректен**.

## Лог `invalid client hello`

Часто это:
- параллельные попытки приложения (QUIC/проверки);
- DPI на пути до **37.230.114.25:443** (Литва на 443 с того же Wi‑Fi работает — типичный паттерн).

Строка `dialing TCP to tcp:check.happ.su:443` — **Happ уже подключился** к inbound; дальше смотрите egress.

## 1. Egress с России

```bash
curl -4 --max-time 5 https://ifconfig.me
curl -I --max-time 5 https://check.happ.su
curl -I --max-time 5 https://www.wikipedia.org
```

Если тут ошибки — direct outbound с России не выходит в интернет.

## 2. Поиск успешных сессий

```bash
journalctl -u xray --since "30 min ago" | grep -E "accepted|544709692"
```

## 3. Вариант A — inbound на **2053**, сайт на **443**

```bash
docker start cv_portfolio_nginx
sudo cp ~/NetAgent/configs/xray-russia-direct-2053.production.json \
  /usr/local/etc/xray/config.json
sudo systemctl restart xray
ss -lntp | grep -E '443|2053'
```

Должно: **docker** на 443, **xray** на 2053.

Ссылка (**порт 2053**):

```
vless://822c54b6-4fae-4043-9774-70cd879c283f@37.230.114.25:2053?encryption=none&type=tcp&security=reality&pbk=j-iuguAzBEJ4-u76nVncqDxBipKnsPgGkBOunpoYBXA&flow=xtls-rprx-vision&sni=www.wikipedia.org&fp=chrome&sid=6ba85179e30d4fc2#NetAgent-RU
```

Тест с iPhone (v2rayTun): Global + DNS Remote. ifconfig.me → `37.230.114.25`.

## 4. v2rayTun — Fragment

В настройках узла: **Fragment ON** (length 100-200, interval 10-20) — иногда помогает на 443 к российским IP.

## 5. Fingerprint

Вручную в клиенте: **chrome** → **ios** или **safari**.

## 6. Relay после direct

`xray-russia-relay-2053.production.json`, inbound port **2053** или **443** (что сработало в direct).

ifconfig.me → `45.93.137.80`.

## Wi‑Fi vs LTE

| Сценарий | Решение |
|----------|---------|
| Литва direct Wi‑Fi | admin link 45.93.137.80 |
| Россия 2053 Wi‑Fi OK | relay на 2053 |
| Россия не работает нигде | другой IP/провайдер VPS в РФ |
