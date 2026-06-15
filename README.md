# NetAgent

MVP platform for selling monthly Xray VLESS Reality VPN subscriptions.

Current implementation focus: **Stage 1 — Xray Agent** and initial **Telegram bot mock flow**.

## Xray Agent

The agent runs on the Lithuanian VPN server and edits:

```text
/usr/local/etc/xray/config.json
```

It exposes a small HTTPS API on port `8443`:

- `GET /health`
- `GET /users`
- `GET /users/count`
- `POST /add_user`
- `POST /remove_user`

Auth is done with the `X-API-Key` header. The billing server IP is whitelisted with
`AGENT_ALLOWED_IPS=37.230.114.25`.

### Local Test

```powershell
pip install -e .[dev]
pytest
```

### CLI

```powershell
$env:XRAY_AGENT_API_KEY="change-me"
python scripts/xray_cli.py count
python scripts/xray_cli.py add --email user_1@netagent.local --limit 2
```

## Telegram Bot

The bot is a separate microservice in `src/bot`. For now it uses in-memory mock billing:

- shows Start / Standard / Family plans
- confirms a mock payment
- generates a stable UUID per Telegram user
- shows subscription status and a mock VLESS URI

Run locally:

```powershell
$env:TELEGRAM_BOT_TOKEN="<bot-token>"
python -m bot.app
```

Run with Docker Compose profile:

```powershell
docker compose -f docker/docker-compose.yml --profile bot up --build bot
```
