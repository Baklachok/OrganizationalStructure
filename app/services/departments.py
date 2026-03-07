from __future__ import annotations

from collections import defaultdict
from typing import Any, Literal

from fastapi import status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentCreate, DepartmentUpdate


def _get_department_or_404(db: Session, department_id: int) -> Department:
    department = db.get(Department, department_id)
    if department is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            "department_not_found",
            "Department not found",
        )
    return department


def _ensure_not_descendant(db: Session, department_id: int, new_parent_id: int) -> None:
    current_id: int | None = new_parent_id
    while current_id is not None:
        if current_id == department_id:
            raise api_error(
                status.HTTP_409_CONFLICT,
                "department_tree_cycle",
                "Cannot create a cycle in department tree",
            )
        current_department = db.get(Department, current_id)
        if current_department is None:
            raise api_error(
                status.HTTP_404_NOT_FOUND,
                "department_not_found",
                "Department not found",
            )
        current_id = current_department.parent_id


def _serialize_department(department: Department) -> dict[str, Any]:
    return {
        "id": department.id,
        "name": department.name,
        "parent_id": department.parent_id,
        "created_at": department.created_at,
    }


def _serialize_employee(employee: Employee) -> dict[str, Any]:
    return {
        "id": employee.id,
        "department_id": employee.department_id,
        "full_name": employee.full_name,
        "position": employee.position,
        "hired_at": employee.hired_at,
        "created_at": employee.created_at,
    }


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    if payload.parent_id is not None:
        _get_department_or_404(db, payload.parent_id)

    department = Department(name=payload.name, parent_id=payload.parent_id)
    db.add(department)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise api_error(
            status.HTTP_409_CONFLICT,
            "department_name_conflict",
            "Department with same name already exists for this parent",
        ) from exc

    db.refresh(department)
    return department


def update_department(db: Session, department_id: int, payload: DepartmentUpdate) -> Department:
    department = _get_department_or_404(db, department_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]
        if new_parent_id == department_id:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                "department_self_parent",
                "Department cannot be parent of itself",
            )
        if new_parent_id is not None:
            _get_department_or_404(db, new_parent_id)
            _ensure_not_descendant(db, department_id, new_parent_id)
        department.parent_id = new_parent_id

    if "name" in update_data:
        department.name = update_data["name"]

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise api_error(
            status.HTTP_409_CONFLICT,
            "department_name_conflict",
            "Department with same name already exists for this parent",
        ) from exc

    db.refresh(department)
    return department


def get_department_tree(
    db: Session,
    department_id: int,
    *,
    depth: int = 1,
    include_employees: bool = True,
) -> dict[str, Any]:
    if depth < 1:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "invalid_depth",
            "Depth must be >= 1",
        )

    root = _get_department_or_404(db, department_id)
    departments_by_id: dict[int, Department] = {root.id: root}
    children_by_parent_id: dict[int, list[Department]] = defaultdict(list)

    current_level_ids: list[int] = [root.id]
    for _ in range(depth):
        if not current_level_ids:
            break

        children = db.scalars(
            select(Department)
            .where(Department.parent_id.in_(current_level_ids))
            .order_by(Department.created_at, Department.id)
        ).all()
        next_level_ids: list[int] = []
        for child in children:
            departments_by_id[child.id] = child
            if child.parent_id is not None:
                children_by_parent_id[child.parent_id].append(child)
            next_level_ids.append(child.id)
        current_level_ids = next_level_ids

    employees_by_department_id: dict[int, list[Employee]] = defaultdict(list)
    if include_employees and departments_by_id:
        employees = db.scalars(
            select(Employee)
            .where(Employee.department_id.in_(list(departments_by_id)))
            .order_by(Employee.full_name, Employee.created_at, Employee.id)
        ).all()
        for employee in employees:
            employees_by_department_id[employee.department_id].append(employee)

    def build_subtree(node: Department) -> dict[str, Any]:
        return {
            "department": _serialize_department(node),
            "employees": [
                _serialize_employee(employee)
                for employee in employees_by_department_id.get(node.id, [])
            ]
            if include_employees
            else [],
            "children": [build_subtree(child) for child in children_by_parent_id.get(node.id, [])],
        }

    return build_subtree(root)


def delete_department(
    db: Session,
    department_id: int,
    *,
    mode: Literal["cascade", "reassign"] = "cascade",
    reassign_to_department_id: int | None = None,
) -> None:
    department = _get_department_or_404(db, department_id)

    if mode not in {"cascade", "reassign"}:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "invalid_deletion_mode",
            "Invalid deletion mode",
        )

    if mode == "cascade" and reassign_to_department_id is not None:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "invalid_reassign_target",
            "reassign_to_department_id is only allowed for reassign mode",
        )

    if mode == "reassign":
        if reassign_to_department_id is None:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                "reassign_target_required",
                "reassign_to_department_id is required for reassign mode",
            )
        if reassign_to_department_id == department_id:
            raise api_error(
                status.HTTP_400_BAD_REQUEST,
                "reassign_target_invalid",
                "Cannot reassign employees to the department being deleted",
            )

        _get_department_or_404(db, reassign_to_department_id)
        _ensure_not_descendant(db, department_id, reassign_to_department_id)

        db.execute(
            update(Employee)
            .where(Employee.department_id == department_id)
            .values(department_id=reassign_to_department_id)
        )

    try:
        db.delete(department)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise api_error(
            status.HTTP_409_CONFLICT,
            "department_delete_conflict",
            "Failed to delete department due to data conflict",
        ) from exc
