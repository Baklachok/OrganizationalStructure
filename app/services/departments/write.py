from __future__ import annotations

from typing import Literal

from fastapi import status
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentCreate, DepartmentUpdate

from .common import ensure_not_descendant, get_department_or_404


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    if payload.parent_id is not None:
        get_department_or_404(db, payload.parent_id)

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
    department = get_department_or_404(db, department_id)
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
            get_department_or_404(db, new_parent_id)
            ensure_not_descendant(db, department_id, new_parent_id)
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


def delete_department(
    db: Session,
    department_id: int,
    *,
    mode: Literal["cascade", "reassign"] = "cascade",
    reassign_to_department_id: int | None = None,
) -> None:
    department = get_department_or_404(db, department_id)

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

        get_department_or_404(db, reassign_to_department_id)
        ensure_not_descendant(db, department_id, reassign_to_department_id)

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
