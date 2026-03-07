#!/usr/bin/env sh
set -eu

echo "Waiting for database..."
python - <<'PY'
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True)
attempts = 60
delay_seconds = 2

for attempt in range(1, attempts + 1):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database is available.")
        break
    except OperationalError as exc:
        if attempt == attempts:
            raise RuntimeError("Database is not available.") from exc
        print(f"Database is not ready ({attempt}/{attempts}). Retrying in {delay_seconds}s...")
        time.sleep(delay_seconds)
PY

echo "Applying migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn app.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}"
