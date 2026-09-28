"""Comprehensive unit and integration test suite for ACTUS event generation."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.actus import ActusContract
from app.models.actus_event import ActusEventGenerationStatus, ActusEventType
from app.repositories.actus_event_repository import actus_event_repository
from app.repositories.actus_repository import actus_repository
from app.repositories.contract_repository import contract_repository
from app.repositories.document_repository import document_repository
from app.services.actus_cycle import add_calendar_months, generate_cycle_dates, parse_iso_datetime
from app.services.actus_event_generator import ActusEventGenerator

client = TestClient(app)

# Deterministic Test Fixtures
PAM_ACTUS_CONTRACT = ActusContract(
    contractID="pam-contract-uuid-1",
    contractType="PAM",
    contractRole="RPA",
    currency="USD",
    notionalPrincipal=Decimal("250000"),
    nominalInterestRate=Decimal("0.055"),
    initialExchangeDate="2027-01-01T00:00:00Z",
    maturityDate="2029-01-01T00:00:00Z",
    statusDate="2027-01-01T00:00:00Z",
    cycleOfInterestPayment="P1M",
    cycleAnchorDateOfInterestPayment="2027-01-01T00:00:00Z",
    cycleOfPrincipalRedemption=None,
    cycleAnchorDateOfPrincipalRedemption=None,
    dayCountConvention="30E360",
)

ANN_ACTUS_CONTRACT = ActusContract(
    contractID="ann-contract-uuid-2",
    contractType="ANN",
    contractRole="RPA",
    currency="INR",
    notionalPrincipal=Decimal("100000"),
    nominalInterestRate=Decimal("0.10"),
    initialExchangeDate="2027-01-01T00:00:00Z",
    maturityDate="2029-01-01T00:00:00Z",
    statusDate="2027-01-01T00:00:00Z",
    cycleOfInterestPayment="P1M",
    cycleAnchorDateOfInterestPayment="2027-01-01T00:00:00Z",
    cycleOfPrincipalRedemption="P1M",
    cycleAnchorDateOfPrincipalRedemption="2027-01-01T00:00:00Z",
    dayCountConvention="30E360",
)

LAM_ACTUS_CONTRACT = ActusContract(
    contractID="lam-contract-uuid-3",
    contractType="LAM",
    contractRole="RPA",
    currency="EUR",
    notionalPrincipal=Decimal("120000"),
    nominalInterestRate=Decimal("0.04"),
    initialExchangeDate="2027-01-01T00:00:00Z",
    maturityDate="2028-01-01T00:00:00Z",
    statusDate="2027-01-01T00:00:00Z",
    cycleOfInterestPayment="P1M",
    cycleAnchorDateOfInterestPayment="2027-01-01T00:00:00Z",
    cycleOfPrincipalRedemption="P1M",
    cycleAnchorDateOfPrincipalRedemption="2027-01-01T00:00:00Z",
    dayCountConvention="30E360",
)


@pytest.fixture(autouse=True)
def clear_repos() -> None:
    """Clear all stored repository records before and after each test."""
    actus_event_repository.clear()
    actus_repository.clear()
    contract_repository.clear()
    document_repository.clear()
    yield
    actus_event_repository.clear()
    actus_repository.clear()
    contract_repository.clear()
    document_repository.clear()


# ============================================================================
# EVENT GENERATION UNIT TESTS
# ============================================================================

def test_1_ied_generation() -> None:
    """Test 1: IED (Initial Exchange Date) event is generated at initialExchangeDate."""
    res = ActusEventGenerator.generate_events(PAM_ACTUS_CONTRACT)
    assert res.generation_status == ActusEventGenerationStatus.GENERATED
    first_event = res.events[0]
    assert first_event.event_type == ActusEventType.IED
    assert first_event.event_time == "2027-01-01T00:00:00Z"
    assert first_event.sequence == 1


def test_2_ip_generation() -> None:
    """Test 2: Periodic IP (Interest Payment) events are generated."""
    res = ActusEventGenerator.generate_events(PAM_ACTUS_CONTRACT)
    ip_events = [e for e in res.events if e.event_type == ActusEventType.IP]
    assert len(ip_events) == 24  # 2 years monthly payments
    assert ip_events[0].event_time == "2027-02-01T00:00:00Z"


def test_3_md_generation() -> None:
    """Test 3: MD (Maturity Date) event is generated at maturityDate."""
    res = ActusEventGenerator.generate_events(PAM_ACTUS_CONTRACT)
    last_event = res.events[-1]
    assert last_event.event_type == ActusEventType.MD
    assert last_event.event_time == "2029-01-01T00:00:00Z"


def test_4_pr_generation_where_applicable() -> None:
    """Test 4: PR (Principal Redemption) events generated for ANN and LAM."""
    res_ann = ActusEventGenerator.generate_events(ANN_ACTUS_CONTRACT)
    pr_ann = [e for e in res_ann.events if e.event_type == ActusEventType.PR]
    assert len(pr_ann) == 24

    res_lam = ActusEventGenerator.generate_events(LAM_ACTUS_CONTRACT)
    pr_lam = [e for e in res_lam.events if e.event_type == ActusEventType.PR]
    assert len(pr_lam) == 12  # 1 year monthly payments


def test_5_pp_not_generated_without_prepayment_info() -> None:
    """Test 5: PP (Principal Prepayment) is NOT generated when no prepayment terms exist."""
    res = ActusEventGenerator.generate_events(ANN_ACTUS_CONTRACT)
    pp_events = [e for e in res.events if e.event_type == ActusEventType.PP]
    assert len(pp_events) == 0


def test_6_events_are_chronological() -> None:
    """Test 6: Events are sorted chronologically with 1-based sequence numbers."""
    res = ActusEventGenerator.generate_events(ANN_ACTUS_CONTRACT)
    for i in range(len(res.events) - 1):
        curr_time = res.events[i].event_time
        next_time = res.events[i + 1].event_time
        assert curr_time <= next_time
        assert res.events[i].sequence == i + 1


def test_7_events_do_not_occur_after_maturity() -> None:
    """Test 7: No events occur after contract maturityDate."""
    res = ActusEventGenerator.generate_events(PAM_ACTUS_CONTRACT)
    maturity_str = PAM_ACTUS_CONTRACT.maturityDate
    for ev in res.events:
        assert ev.event_time <= maturity_str


def test_8_same_input_produces_deterministic_output() -> None:
    """Test 8: Event generation is strictly deterministic for identical input."""
    res1 = ActusEventGenerator.generate_events(ANN_ACTUS_CONTRACT)
    res2 = ActusEventGenerator.generate_events(ANN_ACTUS_CONTRACT)
    assert res1.total_events == res2.total_events
    for e1, e2 in zip(res1.events, res2.events):
        assert e1.event_type == e2.event_type
        assert e1.event_time == e2.event_time


def test_9_monthly_p1m_cycle_works_correctly() -> None:
    """Test 9: Monthly P1M cycle generates expected date intervals."""
    start_dt = parse_iso_datetime("2027-01-01T00:00:00Z")
    end_dt = parse_iso_datetime("2027-04-01T00:00:00Z")
    dates = generate_cycle_dates(start_dt, end_dt, "P1M", start_dt)
    assert len(dates) == 4
    assert dates[0].strftime("%Y-%m-%d") == "2027-01-01"
    assert dates[1].strftime("%Y-%m-%d") == "2027-02-01"
    assert dates[2].strftime("%Y-%m-%d") == "2027-03-01"
    assert dates[3].strftime("%Y-%m-%d") == "2027-04-01"


def test_10_calendar_month_boundaries_handled_correctly() -> None:
    """Test 10: Calendar month end boundaries (Jan 31 -> Feb 28 -> Mar 31) handled without 30-day approximation."""
    dt_jan31 = datetime(2027, 1, 31, 0, 0, 0, tzinfo=timezone.utc)
    dt_feb = add_calendar_months(dt_jan31, 1)
    dt_mar = add_calendar_months(dt_jan31, 2)
    dt_apr = add_calendar_months(dt_jan31, 3)

    assert dt_feb.strftime("%Y-%m-%d") == "2027-02-28"
    assert dt_mar.strftime("%Y-%m-%d") == "2027-03-31"
    assert dt_apr.strftime("%Y-%m-%d") == "2027-04-30"


def test_11_missing_interest_anchor_produces_requires_review() -> None:
    """Test 11: Missing interest payment anchor produces REQUIRES_REVIEW."""
    incomplete = PAM_ACTUS_CONTRACT.model_copy(update={"cycleAnchorDateOfInterestPayment": None})
    res = ActusEventGenerator.generate_events(incomplete)
    assert res.generation_status == ActusEventGenerationStatus.REQUIRES_REVIEW
    assert "cycleAnchorDateOfInterestPayment" in res.missing_attributes


def test_12_missing_principal_redemption_info_produces_requires_review() -> None:
    """Test 12: Missing principal redemption info for ANN produces REQUIRES_REVIEW."""
    incomplete = ANN_ACTUS_CONTRACT.model_copy(update={"cycleOfPrincipalRedemption": None})
    res = ActusEventGenerator.generate_events(incomplete)
    assert res.generation_status == ActusEventGenerationStatus.REQUIRES_REVIEW
    assert "cycleOfPrincipalRedemption" in res.missing_attributes


def test_13_pam_does_not_generate_periodic_principal_redemption() -> None:
    """Test 13: PAM contract does NOT generate periodic PR events."""
    res = ActusEventGenerator.generate_events(PAM_ACTUS_CONTRACT)
    pr_events = [e for e in res.events if e.event_type == ActusEventType.PR]
    assert len(pr_events) == 0


def test_14_ann_uses_applicable_repayment_schedule() -> None:
    """Test 14: ANN generates both periodic IP and periodic PR events."""
    res = ActusEventGenerator.generate_events(ANN_ACTUS_CONTRACT)
    ip_events = [e for e in res.events if e.event_type == ActusEventType.IP]
    pr_events = [e for e in res.events if e.event_type == ActusEventType.PR]
    assert len(ip_events) > 0
    assert len(pr_events) > 0


def test_15_lam_uses_applicable_principal_redemption_schedule() -> None:
    """Test 15: LAM contract uses principal redemption schedule."""
    res = ActusEventGenerator.generate_events(LAM_ACTUS_CONTRACT)
    pr_events = [e for e in res.events if e.event_type == ActusEventType.PR]
    assert len(pr_events) == 12


def test_16_unsupported_contract_type_returns_unsupported() -> None:
    """Test 16: Unsupported contractType returns UNSUPPORTED generation status."""
    unsupported = PAM_ACTUS_CONTRACT.model_copy(update={"contractType": "SWPPV"})
    res = ActusEventGenerator.generate_events(unsupported)
    assert res.generation_status == ActusEventGenerationStatus.UNSUPPORTED


def test_17_invalid_actus_contract_returns_invalid() -> None:
    """Test 17: Invalid dates (start >= end) returns INVALID generation status."""
    invalid = PAM_ACTUS_CONTRACT.model_copy(update={"initialExchangeDate": "2030-01-01T00:00:00Z"})
    res = ActusEventGenerator.generate_events(invalid)
    assert res.generation_status == ActusEventGenerationStatus.INVALID


# ============================================================================
# API INTEGRATION TESTS
# ============================================================================

VALID_ANN_CONTRACT_PAYLOAD = {
    "principal": 100000,
    "currency": "INR",
    "annual_interest_rate": 10.0,
    "start_date": "2027-01-01",
    "maturity_date": "2029-01-01",
    "payment_frequency": "MONTHLY",
    "contract_role": "RPA",
    "description": "Example fixed-rate amortizing loan",
}


def test_18_post_generates_actus_events() -> None:
    """Test 18: POST /api/v1/contracts/{id}/actus/events generates expected event schedule."""
    c_resp = client.post("/api/v1/contracts", json=VALID_ANN_CONTRACT_PAYLOAD)
    contract_id = c_resp.json()["contract_id"]

    # Generate ACTUS mapping first
    client.post(f"/api/v1/contracts/{contract_id}/actus")

    # Generate events
    ev_resp = client.post(f"/api/v1/contracts/{contract_id}/actus/events")
    assert ev_resp.status_code == 200
    data = ev_resp.json()
    assert data["contract_id"] == contract_id
    assert data["generation_status"] == "GENERATED"
    assert data["total_events"] > 0
    assert data["events"][0]["event_type"] == "IED"
    assert data["events"][-1]["event_type"] == "MD"


def test_19_get_retrieves_stored_events() -> None:
    """Test 19: GET /api/v1/contracts/{id}/actus/events retrieves stored events."""
    c_resp = client.post("/api/v1/contracts", json=VALID_ANN_CONTRACT_PAYLOAD)
    contract_id = c_resp.json()["contract_id"]

    client.post(f"/api/v1/contracts/{contract_id}/actus")
    client.post(f"/api/v1/contracts/{contract_id}/actus/events")

    get_resp = client.get(f"/api/v1/contracts/{contract_id}/actus/events")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["contract_id"] == contract_id
    assert data["generation_status"] == "GENERATED"
