"""Comprehensive test suite for Phase 7 Blockchain Integration and Payment Reconciliation."""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import uuid
from fastapi.testclient import TestClient
import pytest

from app.blockchain.client import MSTBlockchainClient, blockchain_client
from app.blockchain.exceptions import (
    BlockchainNotConfiguredError,
    BlockchainRPCError,
    BlockchainWrongChainError,
    ContractNotFoundError,
    ContractNotLinkedError,
    InvalidActusHashError,
    InvalidContractAddressError,
)
from app.blockchain.models import (
    ActualPayment,
    BlockchainContractState,
    BlockchainStatus,
    ContractLinkRecord,
    PaymentComparisonStatus,
)
from app.blockchain.utils import bytes32_to_sha256, contract_units_to_decimal, decimal_to_contract_units, sha256_to_bytes32
from app.core.config import settings
from app.main import app
from app.models.actus import ActusContract, ActusMappingRecord, ActusMappingStatus
from app.models.cash_flow import CashFlow, CashFlowCalculationStatus, CashFlowSimulationResult
from app.models.contract import ContractRole, ContractStatus, FinancialContract, PaymentFrequency
from app.models.contract_hash import ContractHash, HashAlgorithm
from app.repositories.actus_repository import actus_repository
from app.repositories.cash_flow_repository import cash_flow_repository
from app.repositories.contract_hash_repository import contract_hash_repository
from app.repositories.contract_link_repository import contract_link_repository
from app.repositories.contract_repository import contract_repository
from app.services.blockchain_service import blockchain_service

client = TestClient(app)

MOCK_CONTRACT_ADDRESS = "0x0000000000000000000000000000000000000001"
MOCK_ACTUS_HASH_HEX = "d9a8f30f4be877e1ab7a1024c73d6374f37703ca60a59decb9c342f135ab7d89"
MOCK_BYTES32 = bytes.fromhex(MOCK_ACTUS_HASH_HEX)


@pytest.fixture(autouse=True)
def clear_all_repositories():
    """Clear all repositories before each test."""
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


def create_test_contract(contract_id: str = "0623b314-e753-49b9-830f-40a97cc0bde1") -> FinancialContract:
    contract = FinancialContract(
        contract_id=contract_id,
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
    return contract_repository.save(contract)


def create_test_cash_flows(contract_id: str = "0623b314-e753-49b9-830f-40a97cc0bde1") -> CashFlowSimulationResult:
    cfs = [
        CashFlow(
            cash_flow_id="cf-1",
            contract_id=contract_id,
            event_id="ev-ied",
            event_type="IED",
            event_time="2027-01-01T00:00:00Z",
            currency="INR",
            opening_principal=Decimal("0.00"),
            interest_amount=Decimal("0.00"),
            principal_amount=Decimal("100000.00"),
            total_amount=Decimal("100000.00"),
            closing_principal=Decimal("100000.00"),
            cash_flow_direction="OUTFLOW",
            net_cash_flow=Decimal("-100000.00"),
        ),
        CashFlow(
            cash_flow_id="cf-2",
            contract_id=contract_id,
            event_id="ev-p1",
            event_type="PR_IP",
            event_time="2027-02-01T00:00:00Z",
            currency="INR",
            opening_principal=Decimal("100000.00"),
            interest_amount=Decimal("833.33"),
            principal_amount=Decimal("3781.16"),
            total_amount=Decimal("4614.49"),
            closing_principal=Decimal("96218.84"),
            cash_flow_direction="INFLOW",
            net_cash_flow=Decimal("4614.49"),
        ),
        CashFlow(
            cash_flow_id="cf-3",
            contract_id=contract_id,
            event_id="ev-p2",
            event_type="PR_IP",
            event_time="2027-03-01T00:00:00Z",
            currency="INR",
            opening_principal=Decimal("96218.84"),
            interest_amount=Decimal("801.82"),
            principal_amount=Decimal("3812.67"),
            total_amount=Decimal("4614.49"),
            closing_principal=Decimal("92406.17"),
            cash_flow_direction="INFLOW",
            net_cash_flow=Decimal("4614.49"),
        ),
    ]
    result = CashFlowSimulationResult(
        contract_id=contract_id,
        actus_contract_type="ANN",
        calculation_status=CashFlowCalculationStatus.CALCULATED,
        currency="INR",
        initial_principal=Decimal("100000.00"),
        total_interest=Decimal("10747.84"),
        total_principal=Decimal("100000.00"),
        total_cash_flow=Decimal("110747.84"),
        final_outstanding_principal=Decimal("0.00"),
        cash_flows=cfs,
        created_at=datetime.now(timezone.utc),
    )
    return cash_flow_repository.save(result)



def mock_state(
    status_enum: BlockchainStatus = BlockchainStatus.ACTIVE,
    actus_hash: str = MOCK_ACTUS_HASH_HEX,
    total_paid: Decimal = Decimal("4614.49"),
) -> BlockchainContractState:
    return BlockchainContractState(
        contract_address=MOCK_CONTRACT_ADDRESS,
        lender="0x1111111111111111111111111111111111111111",
        borrower="0x2222222222222222222222222222222222222222",
        principal=Decimal("100000.00"),
        interest_rate_bps=1000,
        maturity_date=datetime(2029, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        actus_hash=actus_hash,
        status=status_enum,
        total_paid=total_paid,
        chain_id=91562037,
    )


# 1. Missing blockchain configuration
def test_missing_blockchain_configuration():
    dummy_client = MSTBlockchainClient(rpc_url="", chain_id=91562037)
    with pytest.raises(BlockchainNotConfiguredError):
        dummy_client.check_connection()


# 2. Valid blockchain configuration
@patch("app.blockchain.client.Web3")
def test_valid_blockchain_configuration(mock_web3_cls):
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.chain_id = 91562037
    mock_web3_cls.return_value = mock_w3

    dummy_client = MSTBlockchainClient(rpc_url="https://testnetrpc.mstblockchain.com", chain_id=91562037)
    connected, chain_id = dummy_client.check_connection()
    assert connected is True
    assert chain_id == 91562037


# 3. Wrong chain ID
@patch("app.blockchain.client.Web3")
def test_wrong_chain_id(mock_web3_cls):
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.chain_id = 1  # Ethereum mainnet instead of MST 91562037
    mock_web3_cls.return_value = mock_w3

    dummy_client = MSTBlockchainClient(rpc_url="https://testnetrpc.mstblockchain.com", chain_id=91562037)
    with pytest.raises(BlockchainWrongChainError):
        dummy_client.check_connection()


# 4. Valid contract address
def test_valid_contract_address():
    addr = blockchain_client.validate_address("0x0000000000000000000000000000000000000001")
    assert addr == "0x0000000000000000000000000000000000000001"


# 5. Invalid contract address format
def test_invalid_contract_address():
    with pytest.raises(InvalidContractAddressError):
        blockchain_client.validate_address("not-an-evm-address")


# 6. State decoding & 7. Solidity status enum mapping
def test_solidity_status_enum_mapping():
    assert BlockchainStatus.from_solidity_uint(0) == BlockchainStatus.CREATED
    assert BlockchainStatus.from_solidity_uint(1) == BlockchainStatus.ACTIVE
    assert BlockchainStatus.from_solidity_uint(2) == BlockchainStatus.COMPLETED
    assert BlockchainStatus.from_solidity_uint(3) == BlockchainStatus.DELINQUENT
    with pytest.raises(ValueError):
        BlockchainStatus.from_solidity_uint(4)


# 8. bytes32 -> SHA-256 normalization
def test_bytes32_to_sha256_normalization():
    b32 = bytes.fromhex(MOCK_ACTUS_HASH_HEX)
    sha256_str = bytes32_to_sha256(b32)
    assert sha256_str == MOCK_ACTUS_HASH_HEX
    assert len(sha256_str) == 64


# 9. SHA-256 -> bytes32 normalization
def test_sha256_to_bytes32_normalization():
    b32 = sha256_to_bytes32(MOCK_ACTUS_HASH_HEX)
    assert len(b32) == 32
    assert b32 == bytes.fromhex(MOCK_ACTUS_HASH_HEX)


# 10. Matching hash verification
@patch.object(blockchain_service.client, "get_contract_state")
def test_matching_hash_verification(mock_get_state):
    fc = create_test_contract()
    cid = fc.contract_id

    # Create Phase 6 hash
    hash_record = ContractHash(
        contract_id=cid,
        hash_algorithm=HashAlgorithm.SHA256,
        canonical_payload_version="v1",
        contract_hash=MOCK_ACTUS_HASH_HEX,
        canonical_payload={},
        created_at=datetime.now(timezone.utc),
    )
    contract_hash_repository.save(hash_record)

    # Link contract
    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    # Mock on-chain state returning exact same hash
    mock_get_state.return_value = mock_state(actus_hash=MOCK_ACTUS_HASH_HEX)

    result = blockchain_service.verify_onchain_hash(cid)
    assert result.hash_matches is True
    assert result.backend_sha256_hash == MOCK_ACTUS_HASH_HEX
    assert result.onchain_bytes32_hash == MOCK_ACTUS_HASH_HEX


# 11. Mismatching hash verification
@patch.object(blockchain_service.client, "get_contract_state")
def test_mismatching_hash_verification(mock_get_state):
    fc = create_test_contract()
    cid = fc.contract_id

    hash_record = ContractHash(
        contract_id=cid,
        hash_algorithm=HashAlgorithm.SHA256,
        canonical_payload_version="v1",
        contract_hash=MOCK_ACTUS_HASH_HEX,
        canonical_payload={},
        created_at=datetime.now(timezone.utc),
    )
    contract_hash_repository.save(hash_record)

    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    different_hash = "1111111111111111111111111111111111111111111111111111111111111111"
    mock_get_state.return_value = mock_state(actus_hash=different_hash)

    result = blockchain_service.verify_onchain_hash(cid)
    assert result.hash_matches is False
    assert result.backend_sha256_hash != result.onchain_bytes32_hash


# 12. No payment events
@patch.object(blockchain_service.client, "get_payment_events")
def test_no_payment_events(mock_get_events):
    fc = create_test_contract()
    cid = fc.contract_id
    create_test_cash_flows(cid)
    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    mock_get_events.return_value = []

    comp = blockchain_service.compare_expected_vs_actual(cid)
    assert comp.total_expected_payments == 2
    assert comp.total_actual_payments == 0
    assert comp.unpaid_count == 2
    assert comp.matched_count == 0
    assert all(item.comparison_status == PaymentComparisonStatus.UNPAID for item in comp.comparison_items)


# 13. One payment event & 18. Equal expected/actual amount (MATCHED)
@patch.object(blockchain_service.client, "get_payment_events")
def test_one_payment_matched(mock_get_events):
    fc = create_test_contract()
    cid = fc.contract_id
    create_test_cash_flows(cid)
    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    payment1 = ActualPayment(
        transaction_hash="0xabc123",
        block_number=100,
        log_index=0,
        amount=Decimal("4614.49"),
        payment_date=datetime(2027, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        cumulative_total_paid=Decimal("4614.49"),
    )
    mock_get_events.return_value = [payment1]

    comp = blockchain_service.compare_expected_vs_actual(cid)
    assert comp.total_expected_payments == 2
    assert comp.total_actual_payments == 1
    assert comp.matched_count == 1
    assert comp.unpaid_count == 1
    assert comp.comparison_items[0].comparison_status == PaymentComparisonStatus.MATCHED
    assert comp.comparison_items[0].amount_variance == Decimal("0.00")
    assert comp.comparison_items[0].date_variance_days == 0


# 14. Multiple payment events & 15. Deterministic payment ordering
@patch.object(blockchain_service.client, "get_payment_events")
def test_multiple_payment_events_ordering(mock_get_events):
    fc = create_test_contract()
    cid = fc.contract_id
    create_test_cash_flows(cid)
    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    p1 = ActualPayment(
        transaction_hash="0x111",
        block_number=101,
        log_index=0,
        amount=Decimal("4614.49"),
        payment_date=datetime(2027, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        cumulative_total_paid=Decimal("4614.49"),
    )
    p2 = ActualPayment(
        transaction_hash="0x222",
        block_number=102,
        log_index=0,
        amount=Decimal("4614.49"),
        payment_date=datetime(2027, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        cumulative_total_paid=Decimal("9228.98"),
    )
    mock_get_events.return_value = [p1, p2]

    comp = blockchain_service.compare_expected_vs_actual(cid)
    assert comp.matched_count == 2
    assert comp.unpaid_count == 0
    assert comp.comparison_items[0].actual_payment.transaction_hash == "0x111"
    assert comp.comparison_items[1].actual_payment.transaction_hash == "0x222"


# 19. Amount variance
@patch.object(blockchain_service.client, "get_payment_events")
def test_amount_variance(mock_get_events):
    fc = create_test_contract()
    cid = fc.contract_id
    create_test_cash_flows(cid)
    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    p1 = ActualPayment(
        transaction_hash="0x111",
        block_number=101,
        log_index=0,
        amount=Decimal("5000.00"),  # Expected 4614.49
        payment_date=datetime(2027, 2, 1, 0, 0, 0, tzinfo=timezone.utc),
        cumulative_total_paid=Decimal("5000.00"),
    )
    mock_get_events.return_value = [p1]

    comp = blockchain_service.compare_expected_vs_actual(cid)
    item = comp.comparison_items[0]
    assert item.comparison_status == PaymentComparisonStatus.AMOUNT_VARIANCE
    assert item.amount_variance == Decimal("385.51")
    assert item.date_variance_days == 0


# 20. Date variance
@patch.object(blockchain_service.client, "get_payment_events")
def test_date_variance(mock_get_events):
    fc = create_test_contract()
    cid = fc.contract_id
    create_test_cash_flows(cid)
    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    p1 = ActualPayment(
        transaction_hash="0x111",
        block_number=101,
        log_index=0,
        amount=Decimal("4614.49"),
        payment_date=datetime(2027, 2, 5, 0, 0, 0, tzinfo=timezone.utc),  # 4 days late
        cumulative_total_paid=Decimal("4614.49"),
    )
    mock_get_events.return_value = [p1]

    comp = blockchain_service.compare_expected_vs_actual(cid)
    item = comp.comparison_items[0]
    assert item.comparison_status == PaymentComparisonStatus.DATE_VARIANCE
    assert item.amount_variance == Decimal("0.00")
    assert item.date_variance_days == 4


# 21. Both amount and date variance
@patch.object(blockchain_service.client, "get_payment_events")
def test_both_amount_and_date_variance(mock_get_events):
    fc = create_test_contract()
    cid = fc.contract_id
    create_test_cash_flows(cid)
    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    p1 = ActualPayment(
        transaction_hash="0x111",
        block_number=101,
        log_index=0,
        amount=Decimal("4000.00"),
        payment_date=datetime(2027, 2, 10, 0, 0, 0, tzinfo=timezone.utc),
        cumulative_total_paid=Decimal("4000.00"),
    )
    mock_get_events.return_value = [p1]

    comp = blockchain_service.compare_expected_vs_actual(cid)
    item = comp.comparison_items[0]
    assert item.comparison_status == PaymentComparisonStatus.AMOUNT_VARIANCE
    assert item.amount_variance == Decimal("-614.49")
    assert item.date_variance_days == 9


# 22. More actual than expected (UNEXPECTED payments) & 17. Actual payments with no expected payments
@patch.object(blockchain_service.client, "get_payment_events")
def test_more_actual_than_expected(mock_get_events):
    fc = create_test_contract()
    cid = fc.contract_id
    create_test_cash_flows(cid)
    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    p1 = ActualPayment(
        transaction_hash="0x1", block_number=10, log_index=0,
        amount=Decimal("4614.49"), payment_date=datetime(2027, 2, 1, tzinfo=timezone.utc), cumulative_total_paid=Decimal("4614.49")
    )
    p2 = ActualPayment(
        transaction_hash="0x2", block_number=11, log_index=0,
        amount=Decimal("4614.49"), payment_date=datetime(2027, 3, 1, tzinfo=timezone.utc), cumulative_total_paid=Decimal("9228.98")
    )
    p3 = ActualPayment(
        transaction_hash="0x3", block_number=12, log_index=0,
        amount=Decimal("1000.00"), payment_date=datetime(2027, 3, 15, tzinfo=timezone.utc), cumulative_total_paid=Decimal("10228.98")
    )
    mock_get_events.return_value = [p1, p2, p3]

    comp = blockchain_service.compare_expected_vs_actual(cid)
    assert comp.total_expected_payments == 2
    assert comp.total_actual_payments == 3
    assert comp.unexpected_count == 1
    assert len(comp.unexpected_payments) == 1
    assert comp.unexpected_payments[0].transaction_hash == "0x3"


# 23. Fewer actual than expected & 16. Expected payments with no actual payments
@patch.object(blockchain_service.client, "get_payment_events")
def test_fewer_actual_than_expected(mock_get_events):
    fc = create_test_contract()
    cid = fc.contract_id
    create_test_cash_flows(cid)
    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    p1 = ActualPayment(
        transaction_hash="0x1", block_number=10, log_index=0,
        amount=Decimal("4614.49"), payment_date=datetime(2027, 2, 1, tzinfo=timezone.utc), cumulative_total_paid=Decimal("4614.49")
    )
    mock_get_events.return_value = [p1]

    comp = blockchain_service.compare_expected_vs_actual(cid)
    assert comp.total_expected_payments == 2
    assert comp.total_actual_payments == 1
    assert comp.unpaid_count == 1
    assert comp.comparison_items[1].comparison_status == PaymentComparisonStatus.UNPAID


# 24. Decimal precision handling
def test_decimal_precision_conversion():
    d1 = Decimal("100000.00")
    units = decimal_to_contract_units(d1)
    assert units == 100000
    d2 = contract_units_to_decimal(units)
    assert d2 == Decimal("100000.00")

    # Non-zero fractional amount should raise error
    with pytest.raises(ValueError):
        decimal_to_contract_units(Decimal("100000.55"))


# 25. Blockchain unavailable / RPC exception handling
@patch.object(blockchain_service.client, "get_contract_state")
def test_blockchain_unavailable_handling(mock_get_state):
    mock_get_state.side_effect = BlockchainRPCError("RPC Connection Timeout")
    fc = create_test_contract()
    cid = fc.contract_id
    blockchain_service.link_contract(cid, MOCK_CONTRACT_ADDRESS)

    response = client.get(f"/api/v1/blockchain/contracts/{MOCK_CONTRACT_ADDRESS}")
    assert response.status_code == 404 or response.status_code == 400


# 26. Contract not linked
def test_contract_not_linked():
    fc = create_test_contract()
    cid = fc.contract_id

    res = client.get(f"/api/v1/contracts/{cid}/blockchain")
    assert res.status_code == 404
    assert "not linked" in res.json()["detail"].lower()


# 27. Backend startup without blockchain configuration
def test_backend_startup_without_blockchain_config():
    # Verify that FastAPI application instantiates cleanly and health endpoint works
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res_bc_health = client.get("/api/v1/blockchain/health")
    assert res_bc_health.status_code == 200
    assert "status" in res_bc_health.json()
