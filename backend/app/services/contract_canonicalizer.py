"""Contract Canonicalizer Service for deterministic JSON representation of financial contracts."""

from decimal import Decimal
import json
from typing import Any, Dict, Optional

from app.models.actus import ActusContract
from app.models.contract import FinancialContract


def normalize_decimal_str(val: Any, max_decimals: int = 2) -> str:
    """Convert any Decimal-compatible value into a standardized fixed-precision decimal string."""
    if val is None:
        return ""
    d = Decimal(str(val))
    return f"{d:.{max_decimals}f}"


class ContractCanonicalizer:
    """Service providing canonical payload creation and deterministic JSON serialization.
    
    Adheres strictly to version 'v1' canonicalization rules, excluding non-contractual
    runtime metadata (UUIDs, database keys, created_at timestamps, request IDs).
    """

    VERSION = "v1"

    @classmethod
    def build_canonical_payload(
        cls,
        financial_contract: FinancialContract,
        actus_contract: Optional[ActusContract] = None,
    ) -> Dict[str, Any]:
        """Construct a deterministic allow-listed dictionary of meaningful contractual terms."""
        
        # 1. FinancialContract canonical payload mapping
        fc_payload: Dict[str, Any] = {
            "annual_interest_rate": normalize_decimal_str(financial_contract.annual_interest_rate, 2),
            "contract_role": (
                financial_contract.contract_role.value
                if hasattr(financial_contract.contract_role, "value")
                else str(financial_contract.contract_role)
            ),
            "currency": financial_contract.currency.strip().upper(),
            "description": financial_contract.description.strip() if financial_contract.description else None,
            "maturity_date": financial_contract.maturity_date.isoformat(),
            "payment_frequency": (
                financial_contract.payment_frequency.value
                if hasattr(financial_contract.payment_frequency, "value")
                else str(financial_contract.payment_frequency)
            ),
            "principal": normalize_decimal_str(financial_contract.principal, 2),
            "start_date": financial_contract.start_date.isoformat(),
        }

        # 2. ACTUS contract mapping (if available)
        actus_payload: Optional[Dict[str, Any]] = None
        if actus_contract:
            actus_payload = {
                "contractRole": actus_contract.contractRole,
                "contractType": actus_contract.contractType,
                "currency": actus_contract.currency,
                "cycleAnchorDateOfInterestPayment": actus_contract.cycleAnchorDateOfInterestPayment,
                "cycleAnchorDateOfPrincipalRedemption": actus_contract.cycleAnchorDateOfPrincipalRedemption,
                "cycleOfInterestPayment": actus_contract.cycleOfInterestPayment,
                "cycleOfPrincipalRedemption": actus_contract.cycleOfPrincipalRedemption,
                "dayCountConvention": actus_contract.dayCountConvention,
                "initialExchangeDate": actus_contract.initialExchangeDate,
                "interestCalculationBase": actus_contract.interestCalculationBase,
                "maturityDate": actus_contract.maturityDate,
                "nominalInterestRate": normalize_decimal_str(actus_contract.nominalInterestRate, 4),
                "notionalPrincipal": normalize_decimal_str(actus_contract.notionalPrincipal, 2),
            }

        payload = {
            "actus_contract": actus_payload,
            "canonical_payload_version": cls.VERSION,
            "financial_contract": fc_payload,
        }
        return payload

    @classmethod
    def serialize_canonical_json(cls, payload: Dict[str, Any]) -> str:
        """Serialize canonical payload dictionary into a deterministic JSON string.
        
        Uses sorted keys, no unnecessary whitespace, and UTF-8 encoding compatibility.
        """
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def to_canonical_bytes(cls, payload: Dict[str, Any]) -> bytes:
        """Convert canonical payload to UTF-8 encoded bytes ready for hashing."""
        json_str = cls.serialize_canonical_json(payload)
        return json_str.encode("utf-8")
