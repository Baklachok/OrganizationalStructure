from typing import Any

from app.schemas.error import ErrorResponse

ErrorResponses = dict[int | str, dict[str, Any]]

COMMON_ERROR_RESPONSES: ErrorResponses = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}
