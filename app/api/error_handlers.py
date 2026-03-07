from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _default_error_code(status_code: int) -> str:
    return {
        400: "bad_request",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        500: "internal_error",
    }.get(status_code, f"http_{status_code}")


def _error_payload(
    status_code: int,
    *,
    code: str | None,
    message: str,
    details: Any | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code or _default_error_code(status_code),
            "message": message,
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return payload


async def http_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        detail = exc.detail
    else:
        status_code = 500
        detail = "Internal server error"

    if isinstance(detail, dict):
        code = detail.get("code")
        message = str(detail.get("message") or detail.get("detail") or "Request failed")
        details = detail.get("details")
    else:
        code = None
        message = str(detail) if detail is not None else "Request failed"
        details = None

    return JSONResponse(
        status_code=status_code,
        content=_error_payload(status_code, code=code, message=message, details=details),
    )


async def request_validation_exception_handler(
    _: Request,
    exc: Exception,
) -> JSONResponse:
    details = exc.errors() if isinstance(exc, RequestValidationError) else None
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            422,
            code="validation_error",
            message="Request validation error",
            details=details,
        ),
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=_error_payload(500, code="internal_error", message="Internal server error"),
    )
