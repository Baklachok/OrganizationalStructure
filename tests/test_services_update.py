import pytest
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.departments import create_department, update_department
from fastapi import HTTPException
from sqlalchemy.orm import Session


def test_update_department_rejects_self_parent(db_session: Session) -> None:
    department = create_department(db_session, DepartmentCreate(name="Engineering"))

    with pytest.raises(HTTPException) as exc_info:
        update_department(db_session, department.id, DepartmentUpdate(parent_id=department.id))

    assert exc_info.value.status_code == 400


def test_update_department_rejects_cycle(db_session: Session) -> None:
    root = create_department(db_session, DepartmentCreate(name="Root"))
    child = create_department(db_session, DepartmentCreate(name="Child", parent_id=root.id))

    with pytest.raises(HTTPException) as exc_info:
        update_department(db_session, root.id, DepartmentUpdate(parent_id=child.id))

    assert exc_info.value.status_code == 409
