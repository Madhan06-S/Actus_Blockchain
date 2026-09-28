"""Service layer evaluating rule-based financial risk status and payment reconciliation indicators."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status

from app.blockchain.models import BlockchainStatus, PaymentComparisonStatus
from app.models.risk_status import ContractRiskStatus, FinancialStatusEnum
from app.services.blockchain_service import BlockchainService, blockchain_service


def _parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO date or datetime string into a UTC-aware datetime object."""
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


class RiskStatusService:
    """Business service evaluating factual risk status indicators from Phase 7 reconciliation data."""

    def __init__(self, bc_service: BlockchainService = blockchain_service) -> None:
        self.blockchain_service = bc_service

    def calculate_risk_status(
        self, contract_id: str, evaluation_date: Optional[datetime] = None
    ) -> ContractRiskStatus:
        """Calculate overall financial status and factual reconciliation indicators for a contract."""
        # 1. Determine UTC evaluation timestamp
        if evaluation_date is None:
            eval_dt = datetime.now(timezone.utc)
        else:
            eval_dt = evaluation_date
            if eval_dt.tzinfo is None:
                eval_dt = eval_dt.replace(tzinfo=timezone.utc)

        # 2. Re-use existing Phase 7 comparison, state, and hash verification services
        comparison = self.blockchain_service.compare_expected_vs_actual(contract_id)
        link = self.blockchain_service.get_link(contract_id)
        
        onchain_state = None
        try:
            onchain_state = self.blockchain_service.get_onchain_state(link.blockchain_contract_address)
            blockchain_status = onchain_state.status
        except Exception:
            blockchain_status = None

        hash_verify = None
        try:
            hash_verify = self.blockchain_service.verify_onchain_hash(contract_id)
            hash_matched = hash_verify.hash_matches
        except Exception:
            hash_matched = False

        # 3. Process Unpaid vs Overdue Payment Counts
        unpaid_count = 0
        overdue_count = 0
        has_item_variance = False

        for item in comparison.comparison_items:
            exp_dt = _parse_iso_datetime(item.expected_date)
            if item.actual_payment is None or item.comparison_status == PaymentComparisonStatus.UNPAID:
                if exp_dt.date() <= eval_dt.date():
                    overdue_count += 1
                else:
                    unpaid_count += 1
            else:
                if item.amount_variance and item.amount_variance != Decimal("0"):
                    has_item_variance = True
                if item.date_variance_days and item.date_variance_days != 0:
                    has_item_variance = True

        # 4. Calculate Net Amount Variance
        net_variance = comparison.total_actual_paid - comparison.total_expected_amount
        unexpected_count = comparison.unexpected_count

        # 5. Determine Overall Financial Status by Rule Precedence
        # Rule A: COMPLETED when ACTUS financial schedule is fully satisfied
        if (
            comparison.total_actual_paid >= comparison.total_expected_amount
            and unpaid_count == 0
            and overdue_count == 0
            and unexpected_count == 0
        ):
            overall_status = FinancialStatusEnum.COMPLETED
        # Rule B: OVERDUE if expected payment date has passed without payment
        elif overdue_count > 0:
            overall_status = FinancialStatusEnum.OVERDUE
        # Rule C: DEVIATION_DETECTED if payment variances or unexpected payments exist
        elif has_item_variance or unexpected_count > 0 or (comparison.matched_count > 0 and net_variance != Decimal("0") and unpaid_count == 0):
            overall_status = FinancialStatusEnum.DEVIATION_DETECTED
        # Rule D: ON_TRACK if payments are up to date with no variances and future payments pending
        else:
            overall_status = FinancialStatusEnum.ON_TRACK

        # 6. Generate Factual Human-Readable Status Reasons
        reasons: List[str] = []
        reasons.append(
            f"Total expected payment schedule amount is {comparison.total_expected_amount:.2f} {sim_currency(comparison)} across {comparison.total_expected_payments} expected payments."
        )
        reasons.append(
            f"Total actual amount paid on-chain is {comparison.total_actual_paid:.2f} {sim_currency(comparison)} across {comparison.total_actual_payments} actual payment events."
        )
        reasons.append(f"Net amount variance is {net_variance:+.2f} {sim_currency(comparison)}.")

        if overdue_count > 0:
            reasons.append(f"{overdue_count} expected payment(s) are overdue past the evaluation date.")
        if unpaid_count > 0:
            reasons.append(f"{unpaid_count} expected payment(s) remain unpaid for future scheduled dates.")
        if unexpected_count > 0:
            reasons.append(f"{unexpected_count} unexpected payment event(s) recorded on-chain beyond expected schedule.")
        if has_item_variance:
            reasons.append("Payment amount or date variance detected in recorded payments.")

        if hash_matched:
            reasons.append("Off-chain Phase 6 SHA-256 integrity hash matches on-chain actusHash.")
        else:
            reasons.append("Off-chain SHA-256 hash does not match on-chain actusHash.")

        if blockchain_status:
            reasons.append(f"Blockchain smart contract status is {blockchain_status.value if hasattr(blockchain_status, 'value') else str(blockchain_status)}.")

        reasons.append(f"Overall financial reconciliation status evaluated as {overall_status.value}.")

        return ContractRiskStatus(
            contract_id=contract_id,
            blockchain_contract_address=link.blockchain_contract_address,
            overall_status=overall_status,
            blockchain_status=blockchain_status,
            hash_integrity_matched=hash_matched,
            total_expected_amount=comparison.total_expected_amount,
            total_actual_paid=comparison.total_actual_paid,
            net_amount_variance=net_variance,
            total_expected_payments=comparison.total_expected_payments,
            matched_payment_count=comparison.matched_count,
            unpaid_payment_count=unpaid_count,
            overdue_payment_count=overdue_count,
            unexpected_payment_count=unexpected_count,
            evaluation_date=eval_dt,
            status_reasons=reasons,
        )


def sim_currency(comp: float) -> str:
    """Helper to return currency string or default."""
    return "INR"


# Global default service instance
risk_status_service = RiskStatusService()
