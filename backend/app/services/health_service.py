"""Service for handling application status and health checks."""

from app.core.config import settings
from app.schemas.common import HealthResponse, RootResponse


class HealthService:
    """Service providing health and status checks."""

    @staticmethod
    def get_root_status() -> RootResponse:
        """Return general root status of the application."""
        return RootResponse(
            message=settings.APP_NAME,
            status="running",
        )

    @staticmethod
    def get_health_status() -> HealthResponse:
        """Return system health status."""
        return HealthResponse(status="healthy")
