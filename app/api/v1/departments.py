from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.department import (
    DepartmentCreate,
    DepartmentDeleteQuery,
    DepartmentGetQuery,
    DepartmentRead,
    DepartmentTreeResponse,
    DepartmentUpdate,
)
from app.schemas.employee import EmployeeCreate, EmployeeRead
from app.services.departments import (
    create_department,
    delete_department,
    get_department_tree,
    update_department,
)
from app.services.employees import create_employee

router = APIRouter()


@router.post("/", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department_endpoint(
    payload: DepartmentCreate,
    db: Annotated[Session, Depends(get_db)],
) -> DepartmentRead:
    department = create_department(db, payload)
    return DepartmentRead.model_validate(department)


@router.post(
    "/{department_id}/employees/",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_employee_endpoint(
    department_id: Annotated[int, Path(ge=1)],
    payload: EmployeeCreate,
    db: Annotated[Session, Depends(get_db)],
) -> EmployeeRead:
    employee = create_employee(db, department_id, payload)
    return EmployeeRead.model_validate(employee)


@router.get("/{department_id}", response_model=DepartmentTreeResponse)
def get_department_endpoint(
    department_id: Annotated[int, Path(ge=1)],
    query: Annotated[DepartmentGetQuery, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> DepartmentTreeResponse:
    tree = get_department_tree(
        db,
        department_id,
        depth=query.depth,
        include_employees=query.include_employees,
    )
    return DepartmentTreeResponse.model_validate(tree)


@router.patch("/{department_id}", response_model=DepartmentRead)
def update_department_endpoint(
    department_id: Annotated[int, Path(ge=1)],
    payload: DepartmentUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> DepartmentRead:
    department = update_department(db, department_id, payload)
    return DepartmentRead.model_validate(department)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department_endpoint(
    department_id: Annotated[int, Path(ge=1)],
    query: Annotated[DepartmentDeleteQuery, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    delete_department(
        db,
        department_id,
        mode=query.mode,
        reassign_to_department_id=query.reassign_to_department_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
