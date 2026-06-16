# Деплой xray-agent на литовский сервер

Сервер: `45.93.137.80`  
Назначение: только `xray` + `xray-agent`  
Российский billing/app сервер: `37.230.114.25`

## 1. Предусловия

На сервере уже должен быть установлен и запущен Xray, который читает конфиг:

```bash
/usr/local/etc/xray/config.json
```

Проверка:

```bash
sudo xray run -test -c /usr/local/etc/xray/config.json
sudo systemctl status xray
```

## 2. Подготовить пользователя и директории

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin netagent || true
sudo mkdir -p /opt/netagent /etc/netagent /etc/netagent/certs
sudo chown -R root:root /etc/netagent
```

## 3. Скопировать код

Вариант через git:

```bash
cd /opt
sudo git clone <repo-url> netagent
cd /opt/netagent
```

Вариант через архив:

```bash
sudo mkdir -p /opt/netagent
sudo tar -xzf netagent.tar.gz -C /opt/netagent --strip-components=1
```

## 4. Python-окружение

```bash
cd /opt/netagent
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

Проверка (важно — без этого будет `status=203/EXEC`):

```bash
test -x /opt/netagent/.venv/bin/python && echo "python ok"
/opt/netagent/.venv/bin/python -m uvicorn --version
/opt/netagent/.venv/bin/python -c "import xray_agent; print('xray_agent ok')"
```

Если `python3.11` недоступен, используйте `python3` (3.10+).

## 5. Self-signed HTTPS сертификат

```bash
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/netagent/certs/agent.key \
  -out /etc/netagent/certs/agent.crt \
  -days 3650 \
  -subj "/CN=45.93.137.80"

sudo chmod 600 /etc/netagent/certs/agent.key
sudo chmod 644 /etc/netagent/certs/agent.crt
```

Российский сервер подключается с `XRAY_AGENT_VERIFY_SSL=false`.

## 6. Env-файл

Создать `/etc/netagent/xray-agent.env`:

```bash
sudo nano /etc/netagent/xray-agent.env
```

Пример:

```env
XRAY_CONFIG_PATH=/usr/local/etc/xray/config.json
XRAY_INBOUND_TAG=vless-reality-in
XRAY_MAX_USERS=50
XRAY_RELOAD_CMD=systemctl restart xray
XRAY_PUBLIC_HOST=45.93.137.80

AGENT_API_KEY=<strong-random-api-key>
# Один IP или несколько через запятую (не JSON!)
AGENT_ALLOWED_IPS=37.230.114.25
AGENT_PORT=8443

# Личный VPN client: email и/или uuid через запятую
AGENT_RESERVED_EMAILS=
AGENT_RESERVED_UUIDS=

# Публичный Reality key для генерации vless:// ссылок.
REALITY_PUBLIC_KEY=
```

API-ключ сгенерировать, например:

```bash
openssl rand -hex 32
```

## 7. Права на config.json и restart Xray

Agent должен читать и править `/usr/local/etc/xray/config.json`, а также выполнять:

```bash
systemctl restart xray
```

MVP-вариант: запускать `xray-agent` от `root` через systemd. Это проще, но требует защищённого порта `8443` firewall-ом и сильного `AGENT_API_KEY`.

## 8. Systemd unit

Создать `/etc/systemd/system/netagent-xray-agent.service`:

```ini
[Unit]
Description=NetAgent Xray Agent
After=network.target xray.service

[Service]
Type=simple
WorkingDirectory=/opt/netagent
EnvironmentFile=/etc/netagent/xray-agent.env
# Используйте python -m uvicorn (надёжнее, чем прямой путь к uvicorn)
ExecStart=/opt/netagent/.venv/bin/python -m uvicorn xray_agent.app:app \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile /etc/netagent/certs/agent.key \
  --ssl-certfile /etc/netagent/certs/agent.crt
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> **Важно:** в `--ssl-keyfile` должен быть `agent.key`, в `--ssl-certfile` — `agent.crt`. Если перепутать — сервис тоже не поднимется.

Запуск:

```bash
sudo systemctl daemon-reload
sudo systemctl enable netagent-xray-agent
sudo systemctl start netagent-xray-agent
sudo systemctl status netagent-xray-agent
```

Логи:

```bash
sudo journalctl -u netagent-xray-agent -f
```

## 9. Firewall

Порт VPN `443` открыт всем. Порт Agent `8443` открыт только российскому серверу:

```bash
sudo ufw allow 443/tcp
sudo ufw allow from 37.230.114.25 to any port 8443 proto tcp
sudo ufw deny 8443/tcp
sudo ufw status
```

Если используется другой firewall, правило то же: `8443/tcp` только с `37.230.114.25`.

## 10. Проверка с российского сервера

```bash
export XRAY_AGENT_URL=https://45.93.137.80:8443
export XRAY_AGENT_API_KEY=<strong-random-api-key>
export XRAY_AGENT_VERIFY_SSL=false

python scripts/xray_cli.py health
python scripts/xray_cli.py count
```

Тестовое добавление:

```bash
python scripts/xray_cli.py add \
  --email user_test@netagent.local \
  --uuid 00000000-0000-4000-8000-000000000001 \
  --limit 1
```

Удаление:

```bash
python scripts/xray_cli.py remove \
  --uuid 00000000-0000-4000-8000-000000000001
```

## 11. Важные замечания

- `AGENT_RESERVED_EMAILS` / `AGENT_RESERVED_UUIDS` нужно заполнить для личного VPN client администратора.
- Reserved client не удаляется через `/remove_user` и не входит в лимит 50 платных clients.
- При каждом `/add_user` и `/remove_user` Agent валидирует config и выполняет `systemctl restart xray`.
- Если `xray run -test` не проходит, Agent откатывает config на предыдущую версию.

## 12. Восстановление VPN (если перестал работать)

Выполнить **на литовском сервере** по порядку:

### 12.1 Остановить agent (чтобы не трогал config)

```bash
sudo systemctl stop netagent-xray-agent
sudo systemctl disable netagent-xray-agent
```

### 12.2 Проверить Xray

```bash
sudo xray run -test -c /usr/local/etc/xray/config.json
sudo systemctl status xray
sudo journalctl -u xray -n 50 --no-pager
```

Если `run -test` **ошибка** — config сломан. Восстановить из бэкапа:

```bash
sudo cp /usr/local/etc/xray/config.json /usr/local/etc/xray/config.json.broken.$(date +%F-%H%M)
# если есть бэкап до деплоя:
sudo cp /usr/local/etc/xray/config.json.bak /usr/local/etc/xray/config.json
# или вручную вернуть рабочий clients[] с вашим личным UUID
sudo xray run -test -c /usr/local/etc/xray/config.json
```

### 12.3 Запустить Xray

```bash
sudo systemctl restart xray
sudo systemctl status xray
ss -lntp | grep 443
```

Проверьте VPN с телефона/клиента. **Сначала VPN, потом agent.**

### 12.4 Исправить `203/EXEC` у agent

```bash
ls -la /opt/netagent/.venv/bin/python
ls -la /opt/netagent/.venv/bin/uvicorn
/opt/netagent/.venv/bin/python -m uvicorn --version
```

Если файлов нет — переустановить:

```bash
cd /opt/netagent
python3 -m venv .venv
.venv/bin/pip install -e .
```

Проверить сертификаты:

```bash
ls -la /etc/netagent/certs/
```

Исправить unit (см. раздел 8), затем:

```bash
sudo systemctl daemon-reload
sudo systemctl start netagent-xray-agent
sudo systemctl status netagent-xray-agent
```

## 13. Типичные ошибки

| Симптом | Причина | Решение |
|---------|---------|---------|
| `status=203/EXEC` | Нет `.venv` или uvicorn | `pip install -e .`, `python -m uvicorn` |
| `SettingsError: agent_allowed_ips` | IP в env как `37.230.114.25`, а код ждал JSON | CSV: `AGENT_ALLOWED_IPS=37.230.114.25` или обновить код |
| VPN не работает, xray failed | Битый `config.json` | `xray run -test`, восстановить бэкап |
| Agent OK, VPN OK, API 403 | IP не в whitelist | `AGENT_ALLOWED_IPS=37.230.114.25` |
| SSL error с России | Self-signed | `XRAY_AGENT_VERIFY_SSL=false` |
