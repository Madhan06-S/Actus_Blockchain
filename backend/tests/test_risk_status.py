"""Comprehensive unit and integration test suite for Phase 8 Financial Risk/Status layer."""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import uuid
from fastapi.testclient import TestClient
import pytest

from app.blockchain.models import ActualPayment, BlockchainStatus, PaymentComparisonStatus
from app.main import app
from app.models.cash_flow import CashFlow, CashFlowCalculationStatus, CashFlowSimulationResult
from app.models.contract import ContractRole, ContractStatus, FinancialContract, PaymentFrequency
from app.models.contract_hash import ContractHash, HashAlgorithm
from app.models.risk_status import FinancialStatusEnum
from app.repositories.actus_repository import actus_repository
from app.repositories.cash_flow_repository import cash_flow_repository
from app.repositories.contract_hash_repository import contract_hash_repository
from app.repositories.contract_link_repository import contract_link_repository
from app.repositories.contract_repository import contract_repository
from app.services.blockchain_service import blockchain_service
from app.services.risk_status_service import risk_status_service

client = TestClient(app)
MOCK_ADDRESS = "0x0000000000000000000000000000000000000001"


@pytest.fixture(autouse=True)
def clear_repos():
    """Clear in-memory repositories before each test."""
    contract_repository.clear()
    actus_repository.clear()
    cash_flow_repository.clear()
    contract_hash_repository.clear()
    contract_link_repository.clear()
    yield
    contract_repository.clear()
    actus_repository.clear()
    cash_flow_repository.clear()
    contract_hash_repository.clear()
    contract_link_repository.clear()


def setup_base_contract(cid: str = "847f744d-3a10-41ea-8f63-0c450a60410a") -> FinancialContract:
    fc = FinancialContract(
        contract_id=cid,
        principal=Decimal("100000.00"),
        currency="INR",
        annual_interest_rate=Decimal("10.00"),
        start_date=date(2027, 1, 1),
        maturity_date=date(2029, 1, 1),
        payment_frequency=PaymentFrequency.MONTHLY,
        contract_role=ContractRole.RPA,
        description="Fixed-rate amortizing loan",
        status=ContractStatus.VALIDATED,
        created_at=datetime.now(timezone.utc),
    )
    contract_repository.save(fc)
    blockchain_service.link_contract(cid, MOCK_ADDRESS)
    return fc


def setup_cash_flows(cid: str = "847f744d-3a10-41ea-8f63-0c450a60410a") -> CashFlowSimulationResult:
    cfs = [
        CashFlow(
            cash_flow_id="cf-1", contract_id=cid, event_id="ev-p1", event_type="PR_IP",
            event_time="2027-02-01T00:00:00Z", currency="INR", opening_principal=Decimal("100000.00"),
            interest_amount=Decimal("833.33"), principal_amount=Decimal("3781.16"),
            total_amount=Decimal("4614.49"), closing_principal=Decimal("96218.84"),
            cash_flow_direction="INFLOW", net_cash_flow=Decimal("4614.49"),
        ),
        CashFlow(
            cash_flow_id="cf-2", contract_id=cid, event_id="ev-p2", event_type="PR_IP",
            event_time="2027-03-01T00:00:00Z", currency="INR", opening_principal=Decimal("96218.84"),
            interest_amount=Decimal("801.82"), principal_amount=Decimal("3812.67"),
            total_amount=Decimal("4614.49"), closing_principal=Decimal("92406.17"),
            cash_flow_direction="INFLOW", net_cash_flow=Decimal("4614.49"),
        ),
    ]
    res = CashFlowSimulationResult(
        contract_id=cid, actus_contract_type="ANN", calculation_status=CashFlowCalculationStatus.CALCULATED,
        currency="INR", initial_principal=Decimal("100000.00"), total_interest=Decimal("1635.15"),
        total_principal=Decimal("7593.83"), total_cash_flow=Decimal("9228.98"),
        final_outstanding_principal=Decimal("92406.17"), cash_flows=cfs, created_at=datetime.now(timezone.utc),
    )
    return cash_flow_repository.save(res)


# 1. ON_TRACK: future payments, up to date, no variance
@patch.object(blockchain_service.client, "get_payment_events")
@patch.object(blockchain_service.client, "get_contract_state")
def test_status_on_track(mock_state, mock_events):
    cid = "847f744d-3a10-41ea-8f63-0c450a60410a"
    setup_base_contract(cid)
    setup_cash_flows(cid)

    # Evaluation date before first payment date (Jan 15, 2027)
    eval_date = datetime(2027, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
    mock_events.return_value = []
    mock_state.return_value = MagicMock(status=BlockchainStatus.ACTIVE, actus_hash="111", chain_id=91562037)

    status_res = risk_status_service.calculate_risk_status(cid, evaluation_date=eval_date)
    assert status_res.overall_status == FinancialStatusEnum.ON_TRACK
    assert status_res.unpaid_payment_count == 2
    assert status_res.overdue_payment_count == 0
    assert status_res.unexpected_payment_count == 0


# 2. DEVIATION_DETECTED: payment differs from expected
@patch.object(blockchain_service.client, "get_payment_events")
@patch.object(blockchain_service.client, "get_contract_state")
def test_status_deviation_detected(mock_state, mock_events):
    cid = "847f744d-3a10-41ea-8f63-0c450a60410a"
    setup_base_contract(cid)
    setup_cash_flows(cid)

    # Payment received on Feb 1, but for 4000.00 instead of 4614.49
    eval_date = datetime(2027, 2, 15, 0, 0, 0, tzinfo=timezone.utc)
    p1 = ActualPayment(
        transaction_hash="0x1", block_number=1, log_index=0, amount=Decimal("4000.00"),
        payment_date=datetime(2027, 2, 1, tzinfo=timezone.utc), cumulative_total_paid=Decimal("4000.00"),
    )
    mock_events.return_value = [p1]
    mock_state.return_value = MagicMock(status=BlockchainStatus.ACTIVE, actus_hash="111", chain_id=91562037)

    status_res = risk_status_service.calculate_risk_status(cid, evaluation_date=eval_date)
    assert status_res.overall_status == FinancialStatusEnum.DEVIATION_DETECTED
    assert status_res.net_amount_variance < Decimal("0")


# 3. OVERDUE: payment date passed, missing payment
@patch.object(blockchain_service.client, "get_payment_events")
@patch.object(blockchain_service.client, "get_contract_state")
def test_status_overdue(mock_state, mock_events):
    cid = "847f744d-3a10-41ea-8f63-0c450a60410a"
    setup_base_contract(cid)
    setup_cash_flows(cid)

    # Evaluation date Feb 15, 2027 (past Feb 1 due date)
    eval_date = datetime(2027, 2, 15, 0, 0, 0, tzinfo=timezone.utc)
    mock_events.return_value = []
    mock_state.return_value = MagicMock(status=BlockchainStatus.ACTIVE, actus_hash="111", chain_id=91562037)

    status_res = risk_status_service.calculate_risk_status(cid, evaluation_date=eval_date)
    assert status_res.overall_status == FinancialStatusEnum.OVERDUE
    assert status_res.overdue_payment_count == 1
    assert status_res.unpaid_payment_count == 1


# 4. COMPLETED: total actual >= total expected, no unpaid/overdue
@patch.object(blockchain_service.client, "get_payment_events")
@patch.object(blockchain_service.client, "get_contract_state")
def test_status_completed(mock_state, mock_events):
    cid = "847f744d-3a10-41ea-8f63-0c450a60410a"
    setup_base_contract(cid)
    setup_cash_flows(cid)

    eval_date = datetime(2027, 3, 15, 0, 0, 0, tzinfo=timezone.utc)
    p1 = ActualPayment(
        transaction_hash="0x1", block_number=1, log_index=0, amount=Decimal("4614.49"),
        payment_date=datetime(2027, 2, 1, tzinfo=timezone.utc), cumulative_total_paid=Decimal("4614.49"),
    )
    p2 = ActualPayment(
        transaction_hash="0x2", block_number=2, log_index=0, amount=Decimal("4614.49"),
        payment_date=datetime(2027, 3, 1, tzinfo=timezone.utc), cumulative_total_paid=Decimal("9228.98"),
    )
    mock_events.return_value = [p1, p2]
    mock_state.return_value = MagicMock(status=BlockchainStatus.COMPLETED, actus_hash="111", chain_id=91562037)

    status_res = risk_status_service.calculate_risk_status(cid, evaluation_date=eval_date)
    assert status_res.overall_status == FinancialStatusEnum.COMPLETED
    assert status_res.overdue_payment_count == 0
    assert status_res.unpaid_payment_count == 0


# 5. Blockchain COMPLETED but ACTUS not completed
@patch.object(blockchain_service.client, "get_payment_events")
@patch.object(blockchain_service.client, "get_contract_state")
def test_blockchain_completed_but_actus_not_completed(mock_state, mock_events):
    cid = "847f744d-3a10-41ea-8f63-0c450a60410a"
    setup_base_contract(cid)
    setup_cash_flows(cid)

    # Solidity completes when principal paid (e.g. 100000 paid, but 2nd schedule payment missed)
    eval_date = datetime(2027, 3, 15, 0, 0, 0, tzinfo=timezone.utc)
    p1 = ActualPayment(
        transaction_hash="0x1", block_number=1, log_index=0, amount=Decimal("4614.49"),
        payment_date=datetime(2027, 2, 1, tzinfo=timezone.utc), cumulative_total_paid=Decimal("4614.49"),
    )
    mock_events.return_value = [p1]
    mock_state.return_value = MagicMock(status=BlockchainStatus.COMPLETED, actus_hash="111", chain_id=91562037)

    status_res = risk_status_service.calculate_risk_status(cid, evaluation_date=eval_date)
    assert status_res.blockchain_status == BlockchainStatus.COMPLETED
    assert status_res.overall_status == FinancialStatusEnum.OVERDUE


# 6. Unexpected payment
@patch.object(blockchain_service.client, "get_payment_events")
@patch.object(blockchain_service.client, "get_contract_state")
def test_unexpected_payment(mock_state, mock_events):
    cid = "847f744d-3a10-41ea-8f63-0c450a60410a"
    setup_base_contract(cid)
    setup_cash_flows(cid)  # 2 expected payments

    eval_date = datetime(2027, 3, 15, 0, 0, 0, tzinfo=timezone.utc)
    p1 = ActualPayment(
        transaction_hash="0x1", block_number=1, log_index=0, amount=Decimal("4614.49"),
        payment_date=datetime(2027, 2, 1, tzinfo=timezone.utc), cumulative_total_paid=Decimal("4614.49"),
    )
    p2 = ActualPayment(
        transaction_hash="0x2", block_number=2, log_index=0, amount=Decimal("4614.49"),
        payment_date=datetime(2027, 3, 1, tzinfo=timezone.utc), cumulative_total_paid=Decimal("9228.98"),
    )
    p3 = ActualPayment(
        transaction_hash="0x3", block_number=3, log_index=0, amount=Decimal("1000.00"),
        payment_date=datetime(2027, 3, 10, tzinfo=timezone.utc), cumulative_total_paid=Decimal("10228.98"),
    )
    mock_events.return_value = [p1, p2, p3]
    mock_state.return_value = MagicMock(status=BlockchainStatus.ACTIVE, actus_hash="111", chain_id=91562037)

    status_res = risk_status_service.calculate_risk_status(cid, evaluation_date=eval_date)
    assert status_res.overall_status == FinancialStatusEnum.DEVIATION_DETECTED
    assert status_res.unexpected_payment_count == 1



# 7. Overpayment
@patch.object(blockchain_service.client, "get_payment_events")
@patch.object(blockchain_service.client, "get_contract_state")
def test_overpayment(mock_state, mock_events):
    cid = "847f744d-3a10-41ea-8f63-0c450a60410a"
    setup_base_contract(cid)
    setup_cash_flows(cid)

    eval_date = datetime(2027, 2, 15, 0, 0, 0, tzinfo=timezone.utc)
    p1 = ActualPayment(
        transaction_hash="0x1", block_number=1, log_index=0, amount=Decimal("6000.00"),  # Expected 4614.49
        payment_date=datetime(2027, 2, 1, tzinfo=timezone.utc), cumulative_total_paid=Decimal("6000.00"),
    )
    mock_events.return_value = [p1]
    mock_state.return_value = MagicMock(status=BlockchainStatus.ACTIVE, actus_hash="111", chain_id=91562037)

    status_res = risk_status_service.calculate_risk_status(cid, evaluation_date=eval_date)
    assert status_res.overall_status == FinancialStatusEnum.DEVIATION_DETECTED


# 8. Hash integrity matched
@patch.object(blockchain_service, "verify_onchain_hash")
@patch.object(blockchain_service.client, "get_payment_events")
@patch.object(blockchain_service.client, "get_contract_state")
def test_hash_integrity_matched(mock_state, mock_events, mock_verify):
    cid = "847f744d-3a10-41ea-8f63-0c450a60410a"
    setup_base_contract(cid)
    setup_cash_flows(cid)

    mock_events.return_value = []
    mock_state.return_value = MagicMock(status=BlockchainStatus.ACTIVE, actus_hash="111", chain_id=91562037)
    mock_verify.return_value = MagicMock(hash_matches=True)

    status_res = risk_status_service.calculate_risk_status(cid, evaluation_date=datetime(2027, 1, 15, tzinfo=timezone.utc))
    assert status_res.hash_integrity_matched is True
    assert any("integrity hash matches" in reason for reason in status_res.status_reasons)


# 9. Historical evaluation_date
@patch.object(blockchain_service.client, "get_payment_events")
@patch.object(blockchain_service.client, "get_contract_state")
def test_historical_evaluation_date(mock_state, mock_events):
    cid = "847f744d-3a10-41ea-8f63-0c450a60410a"
    setup_base_contract(cid)
    setup_cash_flows(cid)

    mock_events.return_value = []
    mock_state.return_value = MagicMock(status=BlockchainStatus.ACTIVE, actus_hash="111", chain_id=91562037)

    # Evaluate at Jan 15 (before Feb 1 due date) -> ON_TRACK
    res1 = risk_status_service.calculate_risk_status(cid, evaluation_date=datetime(2027, 1, 15, tzinfo=timezone.utc))
    assert res1.overall_status == FinancialStatusEnum.ON_TRACK

    # Evaluate at Feb 15 (after Feb 1 due date) -> OVERDUE
    res2 = risk_status_service.calculate_risk_status(cid, evaluation_date=datetime(2027, 2, 15, tzinfo=timezone.utc))
    assert res2.overall_status == FinancialStatusEnum.OVERDUE


# 10. API GET /status & Missing link error behavior
def test_api_status_missing_link_404():
    random_cid = str(uuid.uuid4())
    res = client.get(f"/api/v1/contracts/{random_cid}/status")
    assert res.status_code == 404
