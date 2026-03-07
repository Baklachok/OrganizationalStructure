from fastapi import status
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate


def create_employee(db: Session, department_id: int, payload: EmployeeCreate) -> Employee:
    department = db.get(Department, department_id)
    if department is None:
        raise api_error(
            status.HTTP_404_NOT_FOUND,
            "department_not_found",
            "Department not found",
        )

    employee = Employee(
        department_id=department.id,
        full_name=payload.full_name,
        position=payload.position,
        hired_at=payload.hired_at,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee
