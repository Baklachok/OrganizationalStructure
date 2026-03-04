from sqlalchemy.orm import Session

from app.schemas.department import DepartmentCreate, DepartmentUpdate


def create_department(db: Session, payload: DepartmentCreate) -> None:
    raise NotImplementedError


def update_department(db: Session, department_id: int, payload: DepartmentUpdate) -> None:
    raise NotImplementedError
