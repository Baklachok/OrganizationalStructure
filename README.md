# Organizational Structure API

FastAPI-проект для API организационной структуры.

## Stack

- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL
- pytest

## Run With Docker

1. Скопировать переменные окружения:
```bash
cp .env.example .env
```

2. Запустить API и PostgreSQL:
```bash
docker compose up --build
```

3. Проверить API:
- `http://localhost:8000/docs`

Остановить контейнеры:
```bash
docker compose down
```

## Local Checks

Установить dev-зависимости:
```bash
poetry install --extras dev
```

Проверка типизации:
```bash
poetry run mypy
```

Линтинг:
```bash
poetry run ruff check .
```

Покрытие тестов (coverage):
```bash
poetry run pytest --cov=app --cov-report=term-missing
```

## Migrations (Alembic)

Применить миграции:
```bash
poetry run alembic upgrade head
```

Откатить все миграции:
```bash
poetry run alembic downgrade base
```
