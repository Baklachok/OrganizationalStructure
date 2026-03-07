# Organizational Structure API

FastAPI-сервис для управления оргструктурой: департаменты (дерево) и сотрудники.

## Stack

- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL
- pytest

## Быстрый запуск (Docker)

1. Скопировать переменные окружения:
```bash
cp .env.example .env
```

2. Запустить API и PostgreSQL:
```bash
docker compose up --build
```

При старте контейнера API автоматически:
- ждёт готовность PostgreSQL;
- применяет миграции (`alembic upgrade head`);
- запускает Uvicorn.

3. Проверить документацию:
- `http://localhost:8000/docs`

4. Проверить текущую ревизию миграций:
```bash
docker compose exec app alembic current
```

Остановить контейнеры:
```bash
docker compose down
```

## Локальный запуск (без Docker)

Установить dev-зависимости:
```bash
poetry install --extras dev
```

2. Применить миграции:
```bash
poetry run alembic upgrade head
```

3. Запустить API:
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Миграции

Применить:
```bash
poetry run alembic upgrade head
```

Откатить:
```bash
poetry run alembic downgrade base
```

## Проверка через Swagger

Основной сценарий проверки:

1. Открыть `http://localhost:8000/docs`.
2. Проверить, что доступны все методы:
   - `POST /departments/`
   - `POST /departments/{id}/employees/`
   - `GET /departments/{id}`
   - `PATCH /departments/{id}`
   - `DELETE /departments/{id}?mode=...`
3. Выполнить запросы через `Try it out` и проверить коды/контракты ответов.

## Проверки качества

Линтинг:
```bash
poetry run ruff check .
```

Типизация:
```bash
poetry run mypy
```

Тесты:
```bash
pytest -q
```

Покрытие:
```bash
poetry run pytest --cov=app --cov-report=term-missing
```

## Структура проекта

- `app/api` — HTTP-слой (роуты, обработка ошибок, контракты).
- `app/services` — бизнес-логика департаментов и сотрудников.
- `app/schemas` — Pydantic-схемы запросов/ответов и валидация.
- `app/models` — SQLAlchemy-модели.
- `app/db` — подключение к БД и сессии.
- `alembic` — миграции БД.
- `tests` — unit/integration тесты ключевых сценариев.
- `scripts/start.sh` — запуск приложения с проверкой готовности БД и миграциями.
