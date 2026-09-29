"""Comprehensive unit and integration tests for Financial Intelligence engines and endpoints."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.contract import ContractRole, FinancialContract, PaymentFrequency
from app.repositories.actus_repository import actus_repository
from app.repositories.contract_repository import contract_repository
from app.repositories.document_repository import document_repository
from app.services.actus_mapper import ActusMapper

client = TestClient(app)

SAMPLE_CONTRACT_PAYLOAD = {
    "principal": 100000,
    "currency": "INR",
    "annual_interest_rate": 10.0,
    "start_date": "2027-01-01",
    "maturity_date": "2029-01-01",
    "payment_frequency": "MONTHLY",
    "contract_role": "RPA",
    "description": "Example fixed-rate amortizing loan for intelligence testing",
}


@pytest.fixture(autouse=True)
def clear_all_repos() -> None:
    actus_repository.clear()
    contract_repository.clear()
    document_repository.clear()
    yield
    actus_repository.clear()
    contract_repository.clear()
    document_repository.clear()


def create_sample_contract() -> str:
    post_resp = client.post("/api/v1/contracts", json=SAMPLE_CONTRACT_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]
    client.post(f"/api/v1/contracts/{contract_id}/actus")
    return contract_id


# ============================================================================
# AI RISK PREDICTION TESTS
# ============================================================================

def test_risk_prediction_endpoint() -> None:
    """Test GET /api/v1/contracts/{id}/risk returns structured risk prediction."""
    cid = create_sample_contract()
    resp = client.get(f"/api/v1/contracts/{cid}/risk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["contract_id"] == cid
    assert data["risk_category"] in ["LOW", "MEDIUM", "HIGH", "NOT_AVAILABLE"]
    assert "default_probability" in data
    assert len(data["features_used"]) >= 10


def test_risk_prediction_missing_contract_returns_404() -> None:
    """Test risk evaluation for non-existent contract returns 404."""
    resp = client.get("/api/v1/contracts/non-existent-cid/risk")
    assert resp.status_code == 404


# ============================================================================
# LIQUIDITY ENGINE TESTS
# ============================================================================

def test_liquidity_forecast_endpoint() -> None:
    """Test POST /api/v1/liquidity/forecast calculates net yearly liquidity."""
    cid = create_sample_contract()
    payload = {
        "contract_ids": [cid],
        "bank_outflows_by_year": {"2027": 50000.0, "2028": 60000.0},
    }
    resp = client.post("/api/v1/liquidity/forecast", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "forecast" in data
    assert data["overall_status"] in ["SAFE", "DEFICIT_RISK"]
    assert "2027" in data["forecast"]
    assert data["forecast"]["2027"]["portfolio_inflow"] > 0


def test_liquidity_forecast_default_request() -> None:
    """Test liquidity forecast with empty payload defaults to all contracts."""
    create_sample_contract()
    resp = client.post("/api/v1/liquidity/forecast", json={})
    assert resp.status_code == 200
    assert resp.json()["contract_count"] >= 1


# ============================================================================
# SCENARIO STRESS TESTING TESTS
# ============================================================================

def test_stress_test_endpoint() -> None:
    """Test POST /api/v1/contracts/{id}/stress-test simulates rate shock."""
    cid = create_sample_contract()
    payload = {
        "rate_shock_percent": 3.0,
        "scenario_description": "Rate hike of +3%",
    }
    resp = client.post(f"/api/v1/contracts/{cid}/stress-test", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["contract_id"] == cid
    assert data["base_case"]["annual_interest_rate"] == 10.0
    assert data["stressed_case"]["annual_interest_rate"] == 13.0
    assert data["difference"]["additional_interest"] > 0
    assert "risk_impact" in data


# ============================================================================
# NEGOTIATION AGENT TESTS
# ============================================================================

def test_negotiation_endpoint() -> None:
    """Test POST /api/v1/contracts/{id}/negotiation generates proposed terms."""
    cid = create_sample_contract()
    payload = {"objective": "Reduce credit risk"}
    resp = client.post(f"/api/v1/contracts/{cid}/negotiation", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["contract_id"] == cid
    assert data["requires_human_approval"] is True
    assert len(data["optimized_terms"]) > 0
    assert "revised_actus_json" in data


# ============================================================================
# AI CHATBOT TESTS
# ============================================================================

def test_chatbot_endpoint() -> None:
    """Test POST /api/v1/contracts/{id}/chat answers user question using context."""
    cid = create_sample_contract()
    payload = {"message": "Why is this contract showing deviation?"}
    resp = client.post(f"/api/v1/contracts/{cid}/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["contract_id"] == cid
    assert len(data["answer"]) > 0
    assert len(data["sources"]) > 0
