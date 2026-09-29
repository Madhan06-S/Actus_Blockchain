import sys
from pathlib import Path

# Ensure backend directory is in sys.path for top-level app module imports
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.actus import router as actus_router
from app.api.routes.actus_events import router as actus_events_router
from app.api.routes.blockchain import router as blockchain_router
from app.api.routes.cash_flows import router as cash_flows_router
from app.api.routes.contract_hash import router as contract_hash_router
from app.api.routes.contracts import router as contracts_router
from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.risk_status import router as risk_status_router
from app.core.config import settings


def create_application() -> FastAPI:
    """Factory function to initialize and configure the FastAPI app instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="ACTUS-Powered Programmable Financial Contracts Backend",
        version="0.1.0",
        debug=settings.DEBUG,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):(517[0-9]|3000)",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(health_router)
    app.include_router(contracts_router)
    app.include_router(documents_router)
    app.include_router(actus_router)
    app.include_router(actus_events_router)
    app.include_router(cash_flows_router)
    app.include_router(contract_hash_router)
    app.include_router(blockchain_router)
    app.include_router(risk_status_router)

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
