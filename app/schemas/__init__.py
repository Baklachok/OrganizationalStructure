from app.schemas.department import (
    DepartmentCreate,
    DepartmentDeleteQuery,
    DepartmentGetQuery,
    DepartmentRead,
    DepartmentTreeResponse,
    DepartmentUpdate,
)
from app.schemas.employee import EmployeeCreate, EmployeeRead
from app.schemas.error import ErrorDetail, ErrorResponse

__all__ = [
    "DepartmentCreate",
    "DepartmentDeleteQuery",
    "DepartmentGetQuery",
    "DepartmentRead",
    "DepartmentTreeResponse",
    "DepartmentUpdate",
    "ErrorDetail",
    "ErrorResponse",
    "EmployeeCreate",
    "EmployeeRead",
]
