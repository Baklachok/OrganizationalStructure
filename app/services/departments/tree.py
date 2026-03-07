from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.models.department import Department
from app.models.employee import Employee

from .common import get_department_or_404


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

    root = get_department_or_404(db, department_id)
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
