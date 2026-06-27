# Откат: Литва direct (Wi‑Fi), убрать Xray с России

Relay Россия → Литва **не используем**. Возврат к схеме: клиенты → **45.93.137.80:443**.

---

## A. Россия — убрать Xray

```bash
ssh root@37.230.114.25

sudo systemctl stop xray
sudo systemctl disable xray
sudo rm -f /etc/systemd/system/xray.service
sudo systemctl daemon-reload

sudo rm -f /usr/local/etc/xray/config.json
# опционально удалить бинарник:
# sudo rm -f /usr/local/bin/xray

sudo ufw delete allow 2053/tcp
# сайт снова на 443
docker start cv_portfolio_nginx
ss -lntp | grep ':443'
```

### Бот NetAgent — `.env` на России

```env
XRAY_PUBLIC_HOST=45.93.137.80
XRAY_PUBLIC_PORT=443
REALITY_PUBLIC_KEY=YTQ_dIa_739_d6x7OUAs2XjMbpX6UOnWBMkGVtEhi18
REALITY_SHORT_ID=6ba85179e30d4fc2
REALITY_SNI=www.wikipedia.org
```

```bash
cd ~/NetAgent
docker compose exec postgres psql -U netagent -d netagent -c "DELETE FROM devices;"
docker compose up -d --build bot
```

---

## B. Литва — восстановить рабочий config

```bash
ssh root@45.93.137.80

sudo systemctl stop netagent-xray-agent

sudo cp /usr/local/etc/xray/config.json \
  /usr/local/etc/xray/config.json.before-restore.$(date +%F-%H%M)

sudo cp /opt/netagent/configs/xray-lithuania-wifi-working.json \
  /usr/local/etc/xray/config.json
# если репо в другом пути — scp с ПК или nano по файлу в репо

sudo xray run -test -c /usr/local/etc/xray/config.json
sudo chmod 644 /usr/local/etc/xray/config.json
sudo systemctl restart xray
sudo systemctl status xray
ss -lntp | grep ':443'
```

### Agent — reserved (без bridge)

```bash
sudo nano /etc/netagent/xray-agent.env
```

```env
AGENT_RESERVED_EMAILS=admin@netagent.local
AGENT_RESERVED_UUIDS=6f176e02-bae9-4998-8bb4-099cbb76981c
```

Убрать `bridge_russia` из reserved, если добавляли.

```bash
sudo systemctl start netagent-xray-agent
sudo systemctl status netagent-xray-agent
```

---

## C. Ссылки для клиентов (Wi‑Fi)

**Admin:**

```
vless://6f176e02-bae9-4998-8bb4-099cbb76981c@45.93.137.80:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.wikipedia.org&fp=chrome&pbk=YTQ_dIa_739_d6x7OUAs2XjMbpX6UOnWBMkGVtEhi18&sid=6ba85179e30d4fc2&type=tcp#Admin-LT
```

**iPhone (из старого config):**

```
vless://989e7ddf-acc4-4178-99d5-c3b4ea33a613@45.93.137.80:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.wikipedia.org&fp=chrome&pbk=YTQ_dIa_739_d6x7OUAs2XjMbpX6UOnWBMkGVtEhi18&sid=6ba85179e30d4fc2&type=tcp#iPhone-LT
```

UUID `822c54b6-...` (Россия) **не используется** — только литовские UUID выше.

Проверка: Wi‑Fi → ifconfig.me → **45.93.137.80**.

---

## LTE

С LTE прямой Литва может не работать (как было). Relay с России не подошёл — отдельная задача (другий IP/провайдер в РФ).
