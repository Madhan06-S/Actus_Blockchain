"""Service layer managing blockchain linking, on-chain state queries, SHA-256 vs bytes32 hash verification, and Expected-vs-Actual payment reconciliation."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status

from app.blockchain.client import MSTBlockchainClient, blockchain_client
from app.blockchain.exceptions import (
    BlockchainError,
    BlockchainNotConfiguredError,
    ContractNotLinkedError,
)
from app.blockchain.models import (
    ActualPayment,
    BlockchainContractState,
    ContractLinkRecord,
    ExpectedVsActualComparison,
    HashVerificationResult,
    PaymentComparisonItem,
    PaymentComparisonStatus,
)
from app.blockchain.utils import sha256_to_bytes32
from app.core.config import settings
from app.repositories.contract_link_repository import ContractLinkRepository, contract_link_repository
from app.repositories.contract_repository import ContractRepository, contract_repository
from app.services.cash_flow_service import CashFlowService, cash_flow_service
from app.services.contract_hash_service import ContractHashService, contract_hash_service


def _parse_iso_date(dt_str: str) -> datetime:
    """Parse ISO date or datetime string to UTC datetime."""
    try:
        clean_str = dt_str.replace("Z", "+00:00")
        if "T" not in clean_str:
            clean_str = f"{clean_str}T00:00:00+00:00"
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


class BlockchainService:
    """Business service layer for MST Blockchain integration and payment reconciliation."""

    def __init__(
        self,
        client: MSTBlockchainClient = blockchain_client,
        link_repo: ContractLinkRepository = contract_link_repository,
        contract_repo: ContractRepository = contract_repository,
        hash_svc: ContractHashService = contract_hash_service,
        cash_flow_svc: CashFlowService = cash_flow_service,
    ) -> None:
        self.client = client
        self.link_repository = link_repo
        self.contract_repository = contract_repo
        self.hash_service = hash_svc
        self.cash_flow_service = cash_flow_svc

    def link_contract(
        self, contract_id: str, address: str, network_name: str = "MST Testnet"
    ) -> ContractLinkRecord:
        """Link an internal FinancialContract ID to a deployed EVM contract address."""
        domain_contract = self.contract_repository.get_by_id(contract_id)
        if not domain_contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Financial contract with ID '{contract_id}' not found.",
            )

        checksum_addr = self.client.validate_address(address)
        chain_id = self.client.expected_chain_id or settings.MST_CHAIN_ID

        record = ContractLinkRecord(
            contract_id=contract_id,
            blockchain_contract_address=checksum_addr,
            chain_id=chain_id,
            network_name=network_name,
            linked_at=datetime.now(timezone.utc),
        )
        saved = self.link_repository.save(record)
        return saved

    def get_link(self, contract_id: str) -> ContractLinkRecord:
        """Retrieve stored ContractLinkRecord for a given contract ID."""
        record = self.link_repository.get_by_contract_id(contract_id)
        if not record:
            raise ContractNotLinkedError(contract_id)
        return record

    def get_onchain_state(self, address: str) -> BlockchainContractState:
        """Fetch live on-chain state for a given contract address."""
        return self.client.get_contract_state(address)

    def get_payment_events(self, address: str) -> List[ActualPayment]:
        """Fetch PaymentRecorded logs for a given contract address."""
        return self.client.get_payment_events(address)

    def verify_onchain_hash(self, contract_id: str) -> HashVerificationResult:
        """Compare Phase 6 off-chain SHA-256 hash with live on-chain actusHash."""
        # 1. Fetch link
        link = self.get_link(contract_id)

        # 2. Fetch Phase 6 backend hash
        try:
            hash_record = self.hash_service.get_contract_hash(contract_id)
        except HTTPException as exc:
            if exc.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Phase 6 contract hash for contract ID '{contract_id}' not found. Please generate Phase 6 hash first.",
                ) from exc
            raise

        backend_sha256 = hash_record.contract_hash

        # 3. Read on-chain state
        onchain_state = self.client.get_contract_state(link.blockchain_contract_address)
        onchain_sha256 = onchain_state.actus_hash

        # Compare normalized 64-char lowercase hex strings
        matches = backend_sha256.strip().lower() == onchain_sha256.strip().lower()

        return HashVerificationResult(
            contract_id=contract_id,
            blockchain_contract_address=link.blockchain_contract_address,
            backend_sha256_hash=backend_sha256,
            onchain_bytes32_hash=onchain_sha256,
            hash_matches=matches,
            chain_id=onchain_state.chain_id,
        )

    def compare_expected_vs_actual(self, contract_id: str) -> ExpectedVsActualComparison:
        """Perform chronological payment reconciliation between Phase 5 expected cash flows and actual blockchain events."""
        # 1. Fetch link
        link = self.get_link(contract_id)

        # 2. Fetch Phase 5 cash flow simulation result
        sim_result = self.cash_flow_service.repository.get_by_contract_id(contract_id)
        if not sim_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Phase 5 cash-flow simulation for contract ID '{contract_id}' not found. Please run cash-flow simulation first.",
            )


        # Extract payment cash flows (exclude initial disbursement IED and neutral maturity MD)
        expected_cash_flows = [
            cf
            for cf in sim_result.cash_flows
            if cf.event_type not in ["IED", "MD"] and Decimal(str(cf.total_amount)) > Decimal("0")
        ]

        # 3. Read actual on-chain payment events
        actual_payments = self.client.get_payment_events(link.blockchain_contract_address)

        # 4. Perform chronological matching
        comparison_items: List[PaymentComparisonItem] = []
        matched_count = 0
        unpaid_count = 0
        unexpected_count = 0

        # Sort cash flows chronologically
        expected_cash_flows.sort(key=lambda cf: cf.event_time)

        # Reconcile expected payments
        for idx, cf in enumerate(expected_cash_flows, start=1):
            exp_amount = Decimal(str(cf.total_amount))
            exp_principal = Decimal(str(cf.principal_amount))
            exp_interest = Decimal(str(cf.interest_amount))
            exp_dt = _parse_iso_date(cf.event_time)

            if idx - 1 < len(actual_payments):
                act = actual_payments[idx - 1]
                act_amount = Decimal(str(act.amount))
                act_dt = act.payment_date

                amount_var = act_amount - exp_amount
                date_var_days = (act_dt.date() - exp_dt.date()).days

                if amount_var == Decimal("0") and date_var_days == 0:
                    comp_status = PaymentComparisonStatus.MATCHED
                elif amount_var != Decimal("0") and date_var_days == 0:
                    comp_status = PaymentComparisonStatus.AMOUNT_VARIANCE
                elif amount_var == Decimal("0") and date_var_days != 0:
                    comp_status = PaymentComparisonStatus.DATE_VARIANCE
                else:
                    comp_status = PaymentComparisonStatus.AMOUNT_VARIANCE

                matched_count += 1

                item = PaymentComparisonItem(
                    sequence=idx,
                    event_type=cf.event_type,
                    expected_date=cf.event_time,
                    expected_total_amount=exp_amount,
                    expected_principal=exp_principal,
                    expected_interest=exp_interest,
                    actual_payment=act,
                    amount_variance=amount_var,
                    date_variance_days=date_var_days,
                    comparison_status=comp_status,
                )
            else:
                unpaid_count += 1
                item = PaymentComparisonItem(
                    sequence=idx,
                    event_type=cf.event_type,
                    expected_date=cf.event_time,
                    expected_total_amount=exp_amount,
                    expected_principal=exp_principal,
                    expected_interest=exp_interest,
                    actual_payment=None,
                    amount_variance=None,
                    date_variance_days=None,
                    comparison_status=PaymentComparisonStatus.UNPAID,
                )
            comparison_items.append(item)

        # 5. Handle surplus actual payments (UNEXPECTED)
        unexpected_payments: List[ActualPayment] = []
        if len(actual_payments) > len(expected_cash_flows):
            surplus = actual_payments[len(expected_cash_flows):]
            for act in surplus:
                unexpected_count += 1
                unexpected_payments.append(act)

        total_exp_amount = sum((Decimal(str(cf.total_amount)) for cf in expected_cash_flows), Decimal("0"))
        total_act_paid = sum((Decimal(str(act.amount)) for act in actual_payments), Decimal("0"))

        return ExpectedVsActualComparison(
            contract_id=contract_id,
            blockchain_contract_address=link.blockchain_contract_address,
            actus_contract_type=sim_result.actus_contract_type,
            total_expected_payments=len(expected_cash_flows),
            total_actual_payments=len(actual_payments),
            total_expected_amount=total_exp_amount,
            total_actual_paid=total_act_paid,
            matched_count=matched_count,
            unpaid_count=unpaid_count,
            unexpected_count=unexpected_count,
            comparison_items=comparison_items,
            unexpected_payments=unexpected_payments,
            generated_at=datetime.now(timezone.utc),
        )


# Global default service instance
blockchain_service = BlockchainService()
