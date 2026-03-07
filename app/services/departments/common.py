from __future__ import annotations

from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.models.department import Department


def get_department_or_404(db: Session, department_id: int) -> Department:
    department = db.get(Department, department_id)
    if department is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            "department_not_found",
            "Department not found",
        )
    return department


def ensure_not_descendant(db: Session, department_id: int, new_parent_id: int) -> None:
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
