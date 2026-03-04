from fastapi import APIRouter

from app.api.v1.departments import router as departments_router

api_router = APIRouter()
api_router.include_router(departments_router, prefix="/departments", tags=["departments"])
