import asyncio
import json

from app.api.error_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
    unhandled_exception_handler,
)
from app.core.errors import api_error
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request


def _build_request() -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("test", 50000),
        "server": ("test", 80),
    }
    return Request(scope)


def test_http_exception_handler_with_plain_detail() -> None:
    response = asyncio.run(
        http_exception_handler(_build_request(), HTTPException(status_code=404, detail="Not found"))
    )
    payload = json.loads(bytes(response.body).decode("utf-8"))

    assert response.status_code == 404
    assert payload == {"error": {"code": "not_found", "message": "Not found"}}


def test_http_exception_handler_with_structured_detail() -> None:
    response = asyncio.run(
        http_exception_handler(
            _build_request(),
            api_error(409, "department_tree_cycle", "Cannot create a cycle in department tree"),
        )
    )
    payload = json.loads(bytes(response.body).decode("utf-8"))

    assert response.status_code == 409
    assert payload == {
        "error": {
            "code": "department_tree_cycle",
            "message": "Cannot create a cycle in department tree",
        }
    }


def test_request_validation_exception_handler_returns_unified_contract() -> None:
    validation_error = RequestValidationError(
        [{"loc": ["query", "depth"], "msg": "Input should be >= 1", "type": "greater_than_equal"}]
    )
    response = asyncio.run(request_validation_exception_handler(_build_request(), validation_error))
    payload = json.loads(bytes(response.body).decode("utf-8"))

    assert response.status_code == 422
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "Request validation error"
    assert isinstance(payload["error"]["details"], list)


def test_unhandled_exception_handler_returns_internal_error() -> None:
    response = asyncio.run(unhandled_exception_handler(_build_request(), RuntimeError("boom")))
    payload = json.loads(bytes(response.body).decode("utf-8"))

    assert response.status_code == 500
    assert payload == {"error": {"code": "internal_error", "message": "Internal server error"}}
