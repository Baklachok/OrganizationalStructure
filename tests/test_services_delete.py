import pytest
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentCreate
from app.schemas.employee import EmployeeCreate
from app.services.departments import create_department, delete_department
from app.services.employees import create_employee
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session


def test_delete_department_cascade_removes_subtree_and_employees(db_session: Session) -> None:
    root = create_department(db_session, DepartmentCreate(name="Root"))
    child = create_department(db_session, DepartmentCreate(name="Child", parent_id=root.id))

    create_employee(db_session, root.id, EmployeeCreate(full_name="A One", position="Lead"))
    create_employee(db_session, child.id, EmployeeCreate(full_name="B Two", position="Dev"))

    delete_department(db_session, root.id, mode="cascade")

    assert db_session.get(Department, root.id) is None
    assert db_session.get(Department, child.id) is None
    assert db_session.scalars(select(Employee)).all() == []


def test_delete_department_reassign_moves_employees(db_session: Session) -> None:
    source = create_department(db_session, DepartmentCreate(name="Source"))
    target = create_department(db_session, DepartmentCreate(name="Target"))
    employee = create_employee(
        db_session,
        source.id,
        EmployeeCreate(full_name="A One", position="Lead"),
    )

    delete_department(
        db_session,
        source.id,
        mode="reassign",
        reassign_to_department_id=target.id,
    )

    moved_employee = db_session.get(Employee, employee.id)
    assert moved_employee is not None
    assert moved_employee.department_id == target.id
    assert db_session.get(Department, source.id) is None


def test_delete_department_reassign_rejects_descendant_target(db_session: Session) -> None:
    root = create_department(db_session, DepartmentCreate(name="Root"))
    child = create_department(db_session, DepartmentCreate(name="Child", parent_id=root.id))

    create_employee(db_session, root.id, EmployeeCreate(full_name="A One", position="Lead"))

    with pytest.raises(HTTPException) as exc_info:
        delete_department(
            db_session,
            root.id,
            mode="reassign",
            reassign_to_department_id=child.id,
        )

    assert exc_info.value.status_code == 409


def test_delete_department_cascade_rejects_reassign_target(db_session: Session) -> None:
    root = create_department(db_session, DepartmentCreate(name="Root"))
    target = create_department(db_session, DepartmentCreate(name="Target"))

    with pytest.raises(HTTPException) as exc_info:
        delete_department(
            db_session,
            root.id,
            mode="cascade",
            reassign_to_department_id=target.id,
        )

    assert exc_info.value.status_code == 400
