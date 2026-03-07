from datetime import date

import pytest
from app.schemas.department import DepartmentCreate
from app.schemas.employee import EmployeeCreate
from app.services.departments import create_department
from app.services.employees import create_employee
from fastapi import HTTPException
from sqlalchemy.orm import Session


def test_create_department_and_employee(db_session: Session) -> None:
    department = create_department(db_session, DepartmentCreate(name="Engineering"))
    employee = create_employee(
        db_session,
        department.id,
        EmployeeCreate(full_name="Ivan Ivanov", position="Backend", hired_at=date(2024, 1, 10)),
    )

    assert department.id is not None
    assert employee.id is not None
    assert employee.department_id == department.id


def test_create_department_name_conflict_within_same_parent_returns_409(
    db_session: Session,
) -> None:
    parent = create_department(db_session, DepartmentCreate(name="Parent"))
    create_department(db_session, DepartmentCreate(name="Backend", parent_id=parent.id))

    with pytest.raises(HTTPException) as exc_info:
        create_department(db_session, DepartmentCreate(name="Backend", parent_id=parent.id))

    assert exc_info.value.status_code == 409


def test_create_department_same_name_in_different_parents_is_allowed(db_session: Session) -> None:
    parent_one = create_department(db_session, DepartmentCreate(name="Parent One"))
    parent_two = create_department(db_session, DepartmentCreate(name="Parent Two"))

    first = create_department(
        db_session,
        DepartmentCreate(name="Backend", parent_id=parent_one.id),
    )
    second = create_department(
        db_session,
        DepartmentCreate(name="Backend", parent_id=parent_two.id),
    )

    assert first.id != second.id


def test_create_employee_in_missing_department_returns_404(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        create_employee(
            db_session,
            9999,
            EmployeeCreate(full_name="Ivan Ivanov", position="Backend"),
        )

    assert exc_info.value.status_code == 404
