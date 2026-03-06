from __future__ import annotations

import pytest
from app.api.v1.departments import (
    create_department_endpoint,
    create_employee_endpoint,
    delete_department_endpoint,
    get_department_endpoint,
    update_department_endpoint,
)
from app.schemas.department import (
    DepartmentCreate,
    DepartmentDeleteQuery,
    DepartmentGetQuery,
    DepartmentUpdate,
)
from app.schemas.employee import EmployeeCreate
from fastapi import HTTPException
from sqlalchemy.orm import Session


def test_post_departments_endpoint(db_session: Session) -> None:
    payload = DepartmentCreate(name="  Engineering  ")

    result = create_department_endpoint(payload, db_session)

    assert result.id >= 1
    assert result.name == "Engineering"
    assert result.parent_id is None


def test_post_department_employees_endpoint(db_session: Session) -> None:
    department = create_department_endpoint(DepartmentCreate(name="Engineering"), db_session)

    employee = create_employee_endpoint(
        department.id,
        EmployeeCreate(full_name="Ivan Ivanov", position="Backend"),
        db_session,
    )

    assert employee.id >= 1
    assert employee.department_id == department.id
    assert employee.full_name == "Ivan Ivanov"


def test_get_department_endpoint(db_session: Session) -> None:
    root = create_department_endpoint(DepartmentCreate(name="Root"), db_session)
    child = create_department_endpoint(
        DepartmentCreate(name="Child", parent_id=root.id),
        db_session,
    )
    create_employee_endpoint(
        root.id,
        EmployeeCreate(full_name="A One", position="Lead"),
        db_session,
    )

    response = get_department_endpoint(
        root.id,
        DepartmentGetQuery(depth=1, include_employees=True),
        db_session,
    )

    assert response.department.id == root.id
    assert len(response.employees) == 1
    assert len(response.children) == 1
    assert response.children[0].department.id == child.id


def test_patch_department_endpoint_rejects_self_parent(db_session: Session) -> None:
    department = create_department_endpoint(DepartmentCreate(name="Root"), db_session)

    with pytest.raises(HTTPException) as exc_info:
        update_department_endpoint(
            department.id,
            DepartmentUpdate(parent_id=department.id),
            db_session,
        )

    assert exc_info.value.status_code == 400


def test_delete_department_endpoint_reassign(db_session: Session) -> None:
    source = create_department_endpoint(DepartmentCreate(name="Source"), db_session)
    target = create_department_endpoint(DepartmentCreate(name="Target"), db_session)
    employee = create_employee_endpoint(
        source.id,
        EmployeeCreate(full_name="A One", position="Engineer"),
        db_session,
    )

    response = delete_department_endpoint(
        source.id,
        DepartmentDeleteQuery(mode="reassign", reassign_to_department_id=target.id),
        db_session,
    )
    assert response.status_code == 204

    with pytest.raises(HTTPException) as exc_info:
        get_department_endpoint(source.id, DepartmentGetQuery(), db_session)
    assert exc_info.value.status_code == 404

    target_tree = get_department_endpoint(target.id, DepartmentGetQuery(), db_session)
    assert len(target_tree.employees) == 1
    assert target_tree.employees[0].id == employee.id
