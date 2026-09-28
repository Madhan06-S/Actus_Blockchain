"""API routes for system health and root status endpoints."""

from fastapi import APIRouter
from app.schemas.common import HealthResponse, RootResponse
from app.services.health_service import HealthService

router = APIRouter()


@router.get(
    "/",
    response_model=RootResponse,
    summary="Root status endpoint",
)
def read_root() -> RootResponse:
    """Return basic backend application status."""
    return HealthService.get_root_status()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
)
def read_health() -> HealthResponse:
    """Return health check status indicator."""
    return HealthService.get_health_status()
