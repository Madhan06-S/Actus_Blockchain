import sys
from pathlib import Path

# Ensure backend directory is in sys.path for top-level app module imports
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI

from app.api.routes.contracts import router as contracts_router
from app.api.routes.health import router as health_router
from app.core.config import settings


def create_application() -> FastAPI:
    """Factory function to initialize and configure the FastAPI app instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="ACTUS-Powered Programmable Financial Contracts Backend",
        version="0.1.0",
        debug=settings.DEBUG,
    )

    # Register API routers
    app.include_router(health_router)
    app.include_router(contracts_router)

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
