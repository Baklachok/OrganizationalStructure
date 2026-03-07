from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.error_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
    unhandled_exception_handler,
)
from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Organizational Structure API")
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.include_router(api_router)
    return app


app = create_app()
