"""Tests for application health and root status endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root() -> None:
    """Test GET / endpoint returns HTTP 200 and expected status response payload."""
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert "message" in json_data
    assert "status" in json_data
    assert json_data["message"] == "ActuCore Financial Backend"
    assert json_data["status"] == "running"


def test_read_health() -> None:
    """Test GET /health endpoint returns HTTP 200 and healthy status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert "status" in json_data
    assert json_data["status"] == "healthy"


def test_cors_headers_allowed_origin() -> None:
    """Test that CORS headers are returned for allowed frontend origin http://localhost:5173."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"

