from __future__ import annotations

from datetime import date

import pytest
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.employee import EmployeeCreate
from app.services.departments import (
    create_department,
    delete_department,
    get_department_tree,
    update_department,
)
from app.services.employees import create_employee
from fastapi import HTTPException
from sqlalchemy import select
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


def test_create_employee_in_missing_department_returns_404(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        create_employee(
            db_session,
            9999,
            EmployeeCreate(full_name="Ivan Ivanov", position="Backend"),
        )

    assert exc_info.value.status_code == 404


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


def test_get_department_tree_respects_depth_and_include_employees(db_session: Session) -> None:
    root = create_department(db_session, DepartmentCreate(name="Root"))
    child = create_department(db_session, DepartmentCreate(name="Child", parent_id=root.id))
    create_department(db_session, DepartmentCreate(name="Grandchild", parent_id=child.id))

    create_employee(db_session, root.id, EmployeeCreate(full_name="A One", position="Lead"))
    create_employee(db_session, child.id, EmployeeCreate(full_name="B Two", position="Dev"))

    tree_depth_1 = get_department_tree(
        db_session,
        root.id,
        depth=1,
        include_employees=True,
    )
    assert tree_depth_1["department"]["id"] == root.id
    assert len(tree_depth_1["children"]) == 1
    assert tree_depth_1["children"][0]["children"] == []
    assert len(tree_depth_1["employees"]) == 1

    tree_depth_2_without_employees = get_department_tree(
        db_session,
        root.id,
        depth=2,
        include_employees=False,
    )
    assert len(tree_depth_2_without_employees["children"][0]["children"]) == 1
    assert tree_depth_2_without_employees["employees"] == []
    assert tree_depth_2_without_employees["children"][0]["employees"] == []


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
