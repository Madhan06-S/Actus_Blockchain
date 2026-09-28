"""Comprehensive unit and integration test suite for Phase 5 ACTUS Cash-Flow Simulation."""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.actus import ActusContract
from app.models.actus_event import ActusEvent, ActusEventStatus, ActusEventType
from app.models.cash_flow import CashFlowCalculationStatus, CashFlowDirection
from app.repositories.actus_event_repository import actus_event_repository
from app.repositories.actus_repository import actus_repository
from app.repositories.cash_flow_repository import cash_flow_repository
from app.repositories.contract_repository import contract_repository
from app.repositories.document_repository import document_repository
from app.services.cash_flow_calculator import CashFlowCalculator, get_cash_flow_direction

client = TestClient(app)

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

ANN_ACTUS_MODEL = ActusContract(
    contractID="ann-cf-test-uuid",
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


@pytest.fixture(autouse=True)
def clear_all_repos() -> None:
    """Clear repositories before and after each test execution."""
    cash_flow_repository.clear()
    actus_event_repository.clear()
    actus_repository.clear()
    contract_repository.clear()
    document_repository.clear()
    yield
    cash_flow_repository.clear()
    actus_event_repository.clear()
    actus_repository.clear()
    contract_repository.clear()
    document_repository.clear()


# ============================================================================
# UNIT TESTS: CASH FLOW CALCULATOR & AMORTIZATION MATH
# ============================================================================

def test_1_ann_basic_calculation() -> None:
    """Test 1: Basic ANN cash flow calculation generates expected simulation result."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    assert sim.calculation_status == CashFlowCalculationStatus.CALCULATED
    assert sim.actus_contract_type == "ANN"
    assert sim.currency == "INR"
    assert len(sim.cash_flows) > 0


def test_2_initial_principal_exchange_ied() -> None:
    """Test 2: Initial exchange (IED) cash flow represents principal disbursement."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    ied_cf = sim.cash_flows[0]
    assert ied_cf.event_type == "IED"
    assert ied_cf.opening_principal == Decimal("0.00")
    assert ied_cf.principal_amount == Decimal("100000.00")
    assert ied_cf.closing_principal == Decimal("100000.00")
    assert ied_cf.cash_flow_direction == CashFlowDirection.OUTFLOW
    assert ied_cf.net_cash_flow == Decimal("-100000.00")


def test_3_monthly_interest_calculation() -> None:
    """Test 3: Periodic interest amount is calculated correctly for first payment period."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    first_payment_cf = sim.cash_flows[1]
    # Month 1 interest = 100000 * (0.10 / 12) = 833.33
    assert first_payment_cf.interest_amount == Decimal("833.33")


def test_4_principal_reduction_across_periods() -> None:
    """Test 4: Principal amount portion reduces the opening principal for each period."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    cf1 = sim.cash_flows[1]
    cf2 = sim.cash_flows[2]

    assert cf1.closing_principal == cf2.opening_principal
    assert cf1.closing_principal < cf1.opening_principal


def test_5_total_payment_calculation() -> None:
    """Test 5: Total periodic payment equals interest portion plus principal portion."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    for cf in sim.cash_flows[1:-1]:  # Exclude IED and MD
        assert cf.total_amount == (cf.interest_amount + cf.principal_amount)


def test_6_outstanding_principal_decreases_correctly() -> None:
    """Test 6: Outstanding principal balance strictly decreases monotonically."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    payment_cfs = [cf for cf in sim.cash_flows if cf.event_type == "PR_IP"]
    for i in range(len(payment_cfs) - 1):
        assert payment_cfs[i].closing_principal > payment_cfs[i + 1].closing_principal


def test_7_final_outstanding_principal_reaches_zero() -> None:
    """Test 7: Final remaining principal balance reaches exactly Decimal('0.00')."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    assert sim.final_outstanding_principal == Decimal("0.00")


def test_8_final_payment_reconciliation() -> None:
    """Test 8: Final payment period reconciles exact remaining principal balance."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    last_repayment = [cf for cf in sim.cash_flows if cf.event_type == "PR_IP"][-1]
    assert last_repayment.principal_amount == last_repayment.opening_principal
    assert last_repayment.closing_principal == Decimal("0.00")


def test_9_decimal_arithmetic_precision() -> None:
    """Test 9: All monetary fields are exact Decimal instances."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    assert isinstance(sim.initial_principal, Decimal)
    assert isinstance(sim.total_interest, Decimal)
    assert isinstance(sim.total_principal, Decimal)
    assert isinstance(sim.total_cash_flow, Decimal)
    assert isinstance(sim.final_outstanding_principal, Decimal)


def test_10_inr_currency_support() -> None:
    """Test 10: INR currency simulation sets currency attribute properly."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    assert sim.currency == "INR"
    assert sim.cash_flows[0].currency == "INR"


def test_11_monthly_schedule() -> None:
    """Test 11: 2-year monthly contract produces 24 repayment cash flow periods."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    repayments = [cf for cf in sim.cash_flows if cf.event_type == "PR_IP"]
    assert len(repayments) == 24


def test_12_missing_actus_mapping_returns_404() -> None:
    """Test 12: Generating cash flows without prior ACTUS mapping returns HTTP 404."""
    c_resp = client.post("/api/v1/contracts", json=VALID_ANN_CONTRACT_PAYLOAD)
    cid = c_resp.json()["contract_id"]

    resp = client.post(f"/api/v1/contracts/{cid}/actus/cash-flows")
    assert resp.status_code == 404


def test_13_missing_actus_events_returns_404() -> None:
    """Test 13: Generating cash flows without prior ACTUS events returns HTTP 404."""
    c_resp = client.post("/api/v1/contracts", json=VALID_ANN_CONTRACT_PAYLOAD)
    cid = c_resp.json()["contract_id"]

    # Generate ACTUS mapping only, skip events
    client.post(f"/api/v1/contracts/{cid}/actus")

    resp = client.post(f"/api/v1/contracts/{cid}/actus/cash-flows")
    assert resp.status_code == 404


def test_14_unsupported_actus_contract_type() -> None:
    """Test 14: Unsupported contractType (e.g. PAM/LAM) returns CALCULATION_UNSUPPORTED."""
    pam_model = ANN_ACTUS_MODEL.model_copy(update={"contractType": "PAM"})
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(pam_model)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(pam_model, domain_events)
    assert sim.calculation_status == CashFlowCalculationStatus.CALCULATION_UNSUPPORTED
    assert "is not supported in Phase 5" in sim.warnings[0]


def test_15_missing_day_count_convention_requires_review() -> None:
    """Test 15: Missing dayCountConvention returns CALCULATION_REQUIRES_REVIEW."""
    no_daycount = ANN_ACTUS_MODEL.model_copy(update={"dayCountConvention": None})
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(no_daycount)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim = CashFlowCalculator.calculate_cash_flows(no_daycount, domain_events)
    assert sim.calculation_status == CashFlowCalculationStatus.CALCULATION_REQUIRES_REVIEW
    assert "dayCountConvention" in sim.missing_attributes


def test_16_invalid_principal_returns_invalid() -> None:
    """Test 16: Invalid principal (<= 0) returns CALCULATION_INVALID."""
    invalid = ANN_ACTUS_MODEL.model_copy(update={"notionalPrincipal": Decimal("0.00")})
    sim = CashFlowCalculator.calculate_cash_flows(invalid, [])
    assert sim.calculation_status == CashFlowCalculationStatus.CALCULATION_INVALID


def test_17_invalid_interest_rate_returns_invalid() -> None:
    """Test 17: Negative interest rate returns CALCULATION_INVALID."""
    invalid = ANN_ACTUS_MODEL.model_copy(update={"nominalInterestRate": Decimal("-0.05")})
    sim = CashFlowCalculator.calculate_cash_flows(invalid, [])
    assert sim.calculation_status == CashFlowCalculationStatus.CALCULATION_INVALID


def test_18_contract_role_sign_behavior() -> None:
    """Test 18: Role sign helper returns OUTFLOW (-1) for IED and INFLOW (+1) for repayments under RPA."""
    dir_rpa_ied, sign_rpa_ied = get_cash_flow_direction("RPA", "IED")
    assert dir_rpa_ied == CashFlowDirection.OUTFLOW
    assert sign_rpa_ied == Decimal("-1")

    dir_rpa_repay, sign_rpa_repay = get_cash_flow_direction("RPA", "IP")
    assert dir_rpa_repay == CashFlowDirection.INFLOW
    assert sign_rpa_repay == Decimal("1")

    dir_rpl_ied, sign_rpl_ied = get_cash_flow_direction("RPL", "IED")
    assert dir_rpl_ied == CashFlowDirection.INFLOW
    assert sign_rpl_ied == Decimal("1")


def test_19_deterministic_repeated_calculation() -> None:
    """Test 19: Repeated simulation calls for identical input produce identical output."""
    from app.services.actus_event_generator import ActusEventGenerator
    events_res = ActusEventGenerator.generate_events(ANN_ACTUS_MODEL)
    domain_events = [ActusEvent.model_validate(e.model_dump()) for e in events_res.events]

    sim1 = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)
    sim2 = CashFlowCalculator.calculate_cash_flows(ANN_ACTUS_MODEL, domain_events)

    assert sim1.total_interest == sim2.total_interest
    assert sim1.total_principal == sim2.total_principal
    assert sim1.total_cash_flow == sim2.total_cash_flow
    assert len(sim1.cash_flows) == len(sim2.cash_flows)


# ============================================================================
# END-TO-END API TESTS FOR PHASE 5
# ============================================================================

def test_20_post_and_get_cash_flows_api() -> None:
    """Test 20: Full API pipeline (Contract -> ACTUS -> Events -> Cash Flows POST & GET)."""
    # 1. Create contract
    c_resp = client.post("/api/v1/contracts", json=VALID_ANN_CONTRACT_PAYLOAD)
    cid = c_resp.json()["contract_id"]

    # 2. Generate ACTUS mapping
    client.post(f"/api/v1/contracts/{cid}/actus")

    # 3. Generate ACTUS events
    client.post(f"/api/v1/contracts/{cid}/actus/events")

    # 4. Generate cash flows (POST)
    cf_post = client.post(f"/api/v1/contracts/{cid}/actus/cash-flows")
    assert cf_post.status_code == 200
    data_post = cf_post.json()
    assert data_post["contract_id"] == cid
    assert data_post["calculation_status"] == "CALCULATED"
    assert Decimal(str(data_post["final_outstanding_principal"])) == Decimal("0.00")
    assert len(data_post["cash_flows"]) > 0

    # 5. Retrieve cash flows (GET)
    cf_get = client.get(f"/api/v1/contracts/{cid}/actus/cash-flows")
    assert cf_get.status_code == 200
    data_get = cf_get.json()
    assert data_get["contract_id"] == cid
    assert data_get["calculation_status"] == "CALCULATED"
    assert data_get["total_interest"] == data_post["total_interest"]
