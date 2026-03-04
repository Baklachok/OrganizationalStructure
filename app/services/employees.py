from sqlalchemy.orm import Session

from app.schemas.employee import EmployeeCreate


def create_employee(db: Session, department_id: int, payload: EmployeeCreate) -> None:
    raise NotImplementedError
