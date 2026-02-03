"""Main API router combining all route modules."""

from fastapi import APIRouter

from app.api import auth, invoices, health, sync

api_router = APIRouter()

# Include sub-routers
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
)

api_router.include_router(
    invoices.router,
    prefix="/invoices",
    tags=["invoices"],
)

api_router.include_router(
    sync.router,
    prefix="/sync",
    tags=["sync"],
)
