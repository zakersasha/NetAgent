# NetAgent

MVP: продажа месячных подписок (Xray VLESS Reality).

| Компонент | Сервер | Документация |
|-----------|--------|--------------|
| `xray-agent` | Литва `45.93.137.80` | [docs/deploy-lithuania.md](docs/deploy-lithuania.md) |
| PostgreSQL + бот | Россия `37.230.114.25` | [docs/deploy-database.md](docs/deploy-database.md) |

## Россия (Docker)

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f bot
```

PostgreSQL: порт `5432`, единая БД для бота и будущей админки.

## Тесты

```bash
pip install -e ".[dev]"
pytest
```
