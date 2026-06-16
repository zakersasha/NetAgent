# NetAgent

MVP: продажа месячных VPN-подписок (Xray VLESS Reality).

| Компонент | Сервер | Документация |
|-----------|--------|--------------|
| `xray-agent` | Литва `45.93.137.80` | [docs/deploy-lithuania.md](docs/deploy-lithuania.md) |
| Telegram-бот | Россия `37.230.114.25` | [docs/deploy-bot-russia.md](docs/deploy-bot-russia.md) |

## Telegram-бот (Docker)

```bash
cp .env.example .env
# TELEGRAM_BOT_TOKEN=... в .env
docker compose up -d --build
docker compose logs -f bot
```

## Xray Agent CLI (с России на Литву)

```bash
pip install -e .
export XRAY_AGENT_URL=https://45.93.137.80:8443
export XRAY_AGENT_API_KEY=...
export XRAY_AGENT_VERIFY_SSL=false
python scripts/xray_cli.py health
```

## Тесты

```bash
pip install -e ".[dev]"
pytest
```
