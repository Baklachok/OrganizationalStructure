from typing import cast

from app.core.config import get_settings
from app.models.department import Department
from app.models.employee import Employee
from pytest import MonkeyPatch
from sqlalchemy import Table, UniqueConstraint


def test_database_url_from_env_parts(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_HOST", "db")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "org")
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "pass")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.sqlalchemy_database_url == "postgresql+psycopg://user:pass@db:5432/org"
    get_settings.cache_clear()


def test_department_unique_constraint_on_parent_and_name() -> None:
    table = cast(Table, Department.__table__)
    unique_constraints = [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    target = next((c for c in unique_constraints if c.name == "uq_departments_parent_name"), None)

    assert target is not None
    assert [column.name for column in target.columns] == ["parent_id", "name"]


def test_department_indexes_exist() -> None:
    table = cast(Table, Department.__table__)
    index_names = {index.name for index in table.indexes}

    assert "ix_departments_parent_id" in index_names
    assert "ix_departments_created_at" in index_names


def test_employee_indexes_exist() -> None:
    table = cast(Table, Employee.__table__)
    index_names = {index.name for index in table.indexes}

    assert "ix_employees_department_id" in index_names
    assert "ix_employees_full_name" in index_names
    assert "ix_employees_created_at" in index_names
