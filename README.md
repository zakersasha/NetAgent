# NetAgent

MVP: продажа месячных подписок (Xray VLESS Reality).

| Компонент | Сервер | Документация |
|-----------|--------|--------------|
| `xray-agent` | Литва `45.93.137.80` | [docs/deploy-lithuania.md](docs/deploy-lithuania.md) |
| Relay Wi‑Fi+LTE | Литва + Россия `51.250.112.128` | [docs/deploy-relay.md](docs/deploy-relay.md) |
| PostgreSQL + бот / VPN entry | Россия `51.250.112.128` | [docs/deploy-database.md](docs/deploy-database.md) |
| Откат на Литву (Wi‑Fi) | — | [docs/restore-lithuania-wifi.md](docs/restore-lithuania-wifi.md) |

## Россия (Docker)

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f bot
```

PostgreSQL: порт `5432`, единая БД для бота и будущей админки.

Контроль устройств (Stats API): [docs/device-enforcement.md](docs/device-enforcement.md)

## Тесты

```bash
pip install -e ".[dev]"
pytest
```
