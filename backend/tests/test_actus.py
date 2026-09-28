"""Comprehensive unit and integration tests for ACTUS contract mapping."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.actus import ActusMappingStatus
from app.models.contract import ContractRole, FinancialContract, PaymentFrequency
from app.repositories.actus_repository import actus_repository
from app.repositories.contract_repository import contract_repository
from app.repositories.document_repository import document_repository
from app.services.actus_mapper import ActusMapper

client = TestClient(app)

VALID_ANN_PAYLOAD = {
    "principal": 100000,
    "currency": "INR",
    "annual_interest_rate": 10.0,
    "start_date": "2027-01-01",
    "maturity_date": "2029-01-01",
    "payment_frequency": "MONTHLY",
    "contract_role": "RPA",
    "description": "Example fixed-rate amortizing loan",
}

VALID_PAM_PAYLOAD = {
    "principal": 250000,
    "currency": "USD",
    "annual_interest_rate": 5.5,
    "start_date": "2027-06-01",
    "maturity_date": "2030-06-01",
    "payment_frequency": "MONTHLY",
    "contract_role": "RPA",
    "description": "Bullet loan with principal at maturity",
}

AMBIGUOUS_PAYLOAD = {
    "principal": 50000,
    "currency": "EUR",
    "annual_interest_rate": 4.0,
    "start_date": "2027-01-01",
    "maturity_date": "2028-01-01",
    "payment_frequency": "MONTHLY",
    "contract_role": "RPL",
    "description": "General corporate lending agreement",
}


@pytest.fixture(autouse=True)
def clear_all_repos() -> None:
    """Clear repositories before and after each test."""
    actus_repository.clear()
    contract_repository.clear()
    document_repository.clear()
    yield
    actus_repository.clear()
    contract_repository.clear()
    document_repository.clear()


def test_1_valid_contract_maps_successfully() -> None:
    """Test 1: Valid FinancialContract maps successfully to ACTUS representation."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    assert actus_resp.status_code == 200
    data = actus_resp.json()
    assert data["source_contract_id"] == contract_id
    assert data["mapping_status"] == "MAPPED"
    assert data["actus_contract"]["contractType"] == "ANN"


def test_2_principal_maps_to_notional_principal() -> None:
    """Test 2: Principal maps to notionalPrincipal."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    data = actus_resp.json()["actus_contract"]
    assert Decimal(str(data["notionalPrincipal"])) == Decimal("100000")


def test_3_currency_maps_correctly() -> None:
    """Test 3: Currency maps correctly."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    assert actus_resp.json()["actus_contract"]["currency"] == "INR"


def test_4_interest_rate_maps_to_fractional_value() -> None:
    """Test 4: Interest rate (10.0%) maps to fractional nominalInterestRate (0.10)."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    data = actus_resp.json()["actus_contract"]
    assert Decimal(str(data["nominalInterestRate"])) == Decimal("0.10")


def test_5_start_date_maps_to_initial_exchange_date() -> None:
    """Test 5: Start date maps to initialExchangeDate ISO string."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    data = actus_resp.json()["actus_contract"]
    assert data["initialExchangeDate"] == "2027-01-01T00:00:00Z"


def test_6_maturity_date_maps_correctly() -> None:
    """Test 6: Maturity date maps to maturityDate ISO string."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    data = actus_resp.json()["actus_contract"]
    assert data["maturityDate"] == "2029-01-01T00:00:00Z"


def test_7_contract_role_maps_correctly() -> None:
    """Test 7: Contract role maps correctly to contractRole."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    assert actus_resp.json()["actus_contract"]["contractRole"] == "RPA"


def test_8_contract_id_maps_correctly() -> None:
    """Test 8: Source contract_id maps to contractID."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    assert actus_resp.json()["actus_contract"]["contractID"] == contract_id


def test_9_monthly_frequency_maps_to_p1m_cycle() -> None:
    """Test 9: Monthly payment frequency maps to ACTUS 'P1M' cycle representation."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    data = actus_resp.json()["actus_contract"]
    assert data["cycleOfInterestPayment"] == "P1M"
    assert data["cycleOfPrincipalRedemption"] == "P1M"


def test_10_missing_information_does_not_produce_fabricated_values() -> None:
    """Test 10: Missing optional attributes remain None / missing without fabrication."""
    post_resp = client.post("/api/v1/contracts", json=AMBIGUOUS_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    data = actus_resp.json()
    assert data["actus_contract"]["interestCalculationBase"] is None


def test_11_ambiguous_contract_type_requires_review() -> None:
    """Test 11: Insufficient repayment information sets contractType=None and REQUIRES_REVIEW."""
    post_resp = client.post("/api/v1/contracts", json=AMBIGUOUS_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    data = actus_resp.json()
    assert data["mapping_status"] == "REQUIRES_REVIEW"
    assert data["actus_contract"]["contractType"] is None
    assert "contractType" in data["missing_attributes"]
    assert len(data["warnings"]) > 0


def test_12_supported_ann_structure_maps_correctly() -> None:
    """Test 12: Explicitly supported ANN amortizing structure maps contractType to ANN."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    data = actus_resp.json()
    assert data["mapping_status"] == "MAPPED"
    assert data["actus_contract"]["contractType"] == "ANN"
    assert data["actus_contract"]["cycleOfPrincipalRedemption"] == "P1M"


def test_13_supported_pam_structure_maps_correctly() -> None:
    """Test 13: Explicitly supported PAM bullet structure maps contractType to PAM."""
    post_resp = client.post("/api/v1/contracts", json=VALID_PAM_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    actus_resp = client.post(f"/api/v1/contracts/{contract_id}/actus")
    data = actus_resp.json()
    assert data["mapping_status"] == "MAPPED"
    assert data["actus_contract"]["contractType"] == "PAM"
    assert data["actus_contract"]["cycleOfPrincipalRedemption"] is None


def test_14_invalid_contract_id_returns_404() -> None:
    """Test 14: Non-existent contract ID returns 404 Not Found."""
    response = client.post("/api/v1/contracts/non-existent-id/actus")
    assert response.status_code == 404


def test_15_get_mapping_before_generation_returns_404() -> None:
    """Test 15: GET /api/v1/contracts/{id}/actus before POST returns 404 Not Found."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    get_resp = client.get(f"/api/v1/contracts/{contract_id}/actus")
    assert get_resp.status_code == 404


def test_16_get_mapping_after_generation_succeeds() -> None:
    """Test 16: GET /api/v1/contracts/{id}/actus retrieves stored mapping."""
    post_resp = client.post("/api/v1/contracts", json=VALID_ANN_PAYLOAD)
    contract_id = post_resp.json()["contract_id"]

    client.post(f"/api/v1/contracts/{contract_id}/actus")

    get_resp = client.get(f"/api/v1/contracts/{contract_id}/actus")
    assert get_resp.status_code == 200
    assert get_resp.json()["actus_contract"]["contractType"] == "ANN"


def test_17_mapping_is_deterministic() -> None:
    """Test 17: Mapping is deterministic for identical input contract and fixed status date."""
    now_utc = datetime(2027, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    domain_contract = FinancialContract(
        contract_id="fixed-test-uuid",
        principal=Decimal("100000"),
        currency="INR",
        annual_interest_rate=Decimal("10.0"),
        start_date="2027-01-01",
        maturity_date="2029-01-01",
        payment_frequency=PaymentFrequency.MONTHLY,
        contract_role=ContractRole.RPA,
        description="Example fixed-rate amortizing loan",
        created_at=now_utc,
    )

    rec1 = ActusMapper.map_contract(domain_contract, status_date=now_utc)
    rec2 = ActusMapper.map_contract(domain_contract, status_date=now_utc)

    assert rec1.actus_contract.statusDate == rec2.actus_contract.statusDate
    assert rec1.actus_contract.nominalInterestRate == rec2.actus_contract.nominalInterestRate
    assert rec1.actus_contract.contractType == rec2.actus_contract.contractType == "ANN"
