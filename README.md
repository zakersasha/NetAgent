# NetAgent

MVP: продажа месячных подписок (Xray VLESS Reality).

| Компонент | Сервер | Документация |
|-----------|--------|--------------|
| `xray-agent` | Литва `45.93.137.80` | [docs/deploy-lithuania.md](docs/deploy-lithuania.md) |
| PostgreSQL + бот | Россия `37.230.114.25` | [docs/deploy-database.md](docs/deploy-database.md) |
| Вход через Россию (LTE) | Россия → Литва relay | [docs/deploy-russia-relay.md](docs/deploy-russia-relay.md) |

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
