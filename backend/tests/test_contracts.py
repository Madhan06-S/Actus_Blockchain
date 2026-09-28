"""Comprehensive unit and integration tests for Financial Contract validation and APIs."""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.contract_repository import contract_repository

client = TestClient(app)

VALID_LOAN_PAYLOAD = {
    "principal": 100000,
    "currency": "INR",
    "annual_interest_rate": 10.0,
    "start_date": "2027-01-01",
    "maturity_date": "2029-01-01",
    "payment_frequency": "MONTHLY",
    "contract_role": "RPA",
    "description": "Example fixed-rate amortizing loan",
}


@pytest.fixture(autouse=True)
def clear_repo() -> None:
    """Clear repository before and after each test execution."""
    contract_repository.clear()
    yield
    contract_repository.clear()


# ============================================================================
# VALID CASES
# ============================================================================

def test_1_valid_inr_loan() -> None:
    """Test 1: Valid ₹100,000 INR loan creation."""
    response = client.post("/api/v1/contracts", json=VALID_LOAN_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert Decimal(str(data["principal"])) == Decimal("100000")
    assert data["currency"] == "INR"
    assert Decimal(str(data["annual_interest_rate"])) == Decimal("10.0")
    assert data["start_date"] == "2027-01-01"
    assert data["maturity_date"] == "2029-01-01"
    assert data["payment_frequency"] == "MONTHLY"
    assert data["contract_role"] == "RPA"
    assert data["status"] == "VALIDATED"


def test_2_valid_zero_interest() -> None:
    """Test 2: Valid contract with zero interest rate."""
    payload = {**VALID_LOAN_PAYLOAD, "annual_interest_rate": 0.0}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 201
    assert Decimal(str(response.json()["annual_interest_rate"])) == Decimal("0.0")


def test_3_valid_different_principal() -> None:
    """Test 3: Valid contract with a different principal amount."""
    payload = {**VALID_LOAN_PAYLOAD, "principal": 5000000.50, "currency": "USD"}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert Decimal(str(data["principal"])) == Decimal("5000000.50")
    assert data["currency"] == "USD"


# ============================================================================
# INVALID CASES
# ============================================================================

def test_4_invalid_principal_zero() -> None:
    """Test 4: Reject principal = 0."""
    payload = {**VALID_LOAN_PAYLOAD, "principal": 0}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


def test_5_invalid_negative_principal() -> None:
    """Test 5: Reject negative principal."""
    payload = {**VALID_LOAN_PAYLOAD, "principal": -1000}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


def test_6_invalid_negative_interest_rate() -> None:
    """Test 6: Reject negative interest rate."""
    payload = {**VALID_LOAN_PAYLOAD, "annual_interest_rate": -5.0}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


def test_7_invalid_start_date_after_maturity() -> None:
    """Test 7: Reject start date after maturity date."""
    payload = {
        **VALID_LOAN_PAYLOAD,
        "start_date": "2030-01-01",
        "maturity_date": "2029-01-01",
    }
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


def test_8_invalid_start_date_equal_maturity() -> None:
    """Test 8: Reject start date equal to maturity date."""
    payload = {
        **VALID_LOAN_PAYLOAD,
        "start_date": "2029-01-01",
        "maturity_date": "2029-01-01",
    }
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


def test_9_invalid_missing_principal() -> None:
    """Test 9: Reject payload missing principal field."""
    payload = {k: v for k, v in VALID_LOAN_PAYLOAD.items() if k != "principal"}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


def test_10_invalid_missing_maturity_date() -> None:
    """Test 10: Reject payload missing maturity_date field."""
    payload = {k: v for k, v in VALID_LOAN_PAYLOAD.items() if k != "maturity_date"}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


def test_11_invalid_payment_frequency() -> None:
    """Test 11: Reject unsupported payment frequency."""
    payload = {**VALID_LOAN_PAYLOAD, "payment_frequency": "WEEKLY"}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


def test_12_invalid_contract_role() -> None:
    """Test 12: Reject invalid contract role."""
    payload = {**VALID_LOAN_PAYLOAD, "contract_role": "INVALID_ROLE"}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


def test_13_invalid_date_format() -> None:
    """Test 13: Reject malformed date format."""
    payload = {**VALID_LOAN_PAYLOAD, "start_date": "01-01-2027"}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


def test_14_invalid_empty_currency() -> None:
    """Test 14: Reject empty currency string."""
    payload = {**VALID_LOAN_PAYLOAD, "currency": "   "}
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

def test_15_post_creates_contract_201() -> None:
    """Test 15: POST creates contract and returns HTTP 201 Created."""
    response = client.post("/api/v1/contracts", json=VALID_LOAN_PAYLOAD)
    assert response.status_code == 201


def test_16_created_contract_has_unique_uuid() -> None:
    """Test 16: Created contract receives a valid UUID contract_id."""
    response = client.post("/api/v1/contracts", json=VALID_LOAN_PAYLOAD)
    data = response.json()
    assert "contract_id" in data
    assert len(data["contract_id"]) == 36  # Standard UUID string length


def test_17_created_contract_has_utc_timestamp() -> None:
    """Test 17: Created contract receives created_at timestamp."""
    response = client.post("/api/v1/contracts", json=VALID_LOAN_PAYLOAD)
    data = response.json()
    assert "created_at" in data
    assert data["created_at"] is not None


def test_18_get_by_id_returns_correct_contract() -> None:
    """Test 18: GET /api/v1/contracts/{id} returns the correct contract."""
    post_resp = client.post("/api/v1/contracts", json=VALID_LOAN_PAYLOAD)
    created = post_resp.json()
    contract_id = created["contract_id"]

    get_resp = client.get(f"/api/v1/contracts/{contract_id}")
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["contract_id"] == contract_id
    assert Decimal(str(fetched["principal"])) == Decimal("100000")


def test_19_get_unknown_id_returns_404() -> None:
    """Test 19: GET unknown contract ID returns 404 Not Found."""
    response = client.get("/api/v1/contracts/non-existent-uuid-12345")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_20_get_all_returns_stored_contracts() -> None:
    """Test 20: GET /api/v1/contracts returns list of stored contracts."""
    client.post("/api/v1/contracts", json=VALID_LOAN_PAYLOAD)
    client.post("/api/v1/contracts", json={**VALID_LOAN_PAYLOAD, "principal": 200000})

    response = client.get("/api/v1/contracts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["contracts"]) == 2


def test_21_two_contracts_receive_different_ids() -> None:
    """Test 21: Two created contracts receive unique, distinct IDs."""
    resp1 = client.post("/api/v1/contracts", json=VALID_LOAN_PAYLOAD)
    resp2 = client.post("/api/v1/contracts", json=VALID_LOAN_PAYLOAD)

    id1 = resp1.json()["contract_id"]
    id2 = resp2.json()["contract_id"]
    assert id1 != id2
