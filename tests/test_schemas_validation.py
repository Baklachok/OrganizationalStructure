import pytest
from app.schemas.department import (
    DepartmentCreate,
    DepartmentDeleteQuery,
    DepartmentGetQuery,
    DepartmentUpdate,
)
from app.schemas.employee import EmployeeCreate
from pydantic import ValidationError


def test_department_name_is_trimmed_on_create() -> None:
    payload = DepartmentCreate(name="  Finance  ")
    assert payload.name == "Finance"


def test_department_name_rejects_whitespace_only() -> None:
    with pytest.raises(ValidationError):
        DepartmentCreate(name="   ")


def test_department_name_is_trimmed_on_update() -> None:
    payload = DepartmentUpdate(name="  Finance  ")
    assert payload.name == "Finance"


def test_employee_fields_are_trimmed() -> None:
    payload = EmployeeCreate(full_name="  Ivan Ivanov  ", position="  Developer  ")
    assert payload.full_name == "Ivan Ivanov"
    assert payload.position == "Developer"


def test_department_get_query_defaults() -> None:
    query = DepartmentGetQuery()
    assert query.depth == 1
    assert query.include_employees is True


def test_department_get_query_depth_max_limit() -> None:
    with pytest.raises(ValidationError):
        DepartmentGetQuery(depth=6)


def test_department_delete_query_requires_reassign_target() -> None:
    with pytest.raises(ValidationError):
        DepartmentDeleteQuery(mode="reassign")


def test_department_delete_query_reassign_target_forbidden_in_cascade_mode() -> None:
    with pytest.raises(ValidationError):
        DepartmentDeleteQuery(mode="cascade", reassign_to_department_id=3)


def test_department_delete_query_reassign_mode_is_valid_with_target() -> None:
    query = DepartmentDeleteQuery(mode="reassign", reassign_to_department_id=3)
    assert query.mode == "reassign"
    assert query.reassign_to_department_id == 3
