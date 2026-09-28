"""ACTUS Contract Mapper Service translating FinancialContract objects into standard ACTUS representations."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple

from app.models.actus import ActusContract, ActusMappingRecord, ActusMappingStatus
from app.models.contract import FinancialContract, PaymentFrequency


def payment_frequency_to_actus_cycle(frequency: PaymentFrequency) -> Optional[str]:
    """Convert application payment frequency enum to standard ACTUS cycle format (ISO 8601 duration)."""
    if frequency == PaymentFrequency.MONTHLY:
        return "P1M"
    return None


class ActusMapper:
    """Mapper translating domain FinancialContract instances into official ACTUS Data Dictionary models."""

    @classmethod
    def map_contract(
        cls, contract: FinancialContract, status_date: Optional[datetime] = None
    ) -> ActusMappingRecord:
        """Translate a validated FinancialContract into an ActusMappingRecord.
        
        If status_date is omitted, defaults to current UTC timestamp.
        Returns MAPPED when contractType can be derived, or REQUIRES_REVIEW if repayment structure is ambiguous.
        """
        warnings: List[str] = []
        missing_attributes: List[str] = []

        # Determine status date
        if status_date is None:
            eval_status_date = datetime.now(timezone.utc)
        else:
            eval_status_date = status_date

        status_date_str = eval_status_date.isoformat().replace("+00:00", "Z")
        initial_exchange_date_str = f"{contract.start_date.isoformat()}T00:00:00Z"
        maturity_date_str = f"{contract.maturity_date.isoformat()}T00:00:00Z"

        # 1. Convert Annual Interest Rate Percentage (e.g. 10.0) to Fraction (e.g. 0.10)
        nominal_interest_rate = contract.annual_interest_rate / Decimal("100")

        # 2. Derive ACTUS Payment Cycle
        interest_cycle = payment_frequency_to_actus_cycle(contract.payment_frequency)
        if not interest_cycle:
            warnings.append(f"Payment frequency '{contract.payment_frequency}' could not be converted to a valid ACTUS cycle.")
            missing_attributes.append("cycleOfInterestPayment")

        # 3. Classify Contract Type based on explicit description / repayment structure
        contract_type, classification_warning = cls._classify_contract_type(contract)
        if classification_warning:
            warnings.append(classification_warning)

        if not contract_type:
            missing_attributes.append("contractType")

        # Determine Principal Redemption Cycle based on Contract Type
        principal_cycle: Optional[str] = None
        if contract_type in ["ANN", "LAM"]:
            principal_cycle = interest_cycle
        elif contract_type == "PAM":
            principal_cycle = None  # Principal repaid at maturity

        day_count_convention = "30E360" if contract_type else None

        # 4. Construct ACTUS Contract representation
        actus_contract = ActusContract(
            contractID=contract.contract_id,
            contractType=contract_type,
            contractRole=contract.contract_role.value if hasattr(contract.contract_role, "value") else str(contract.contract_role),
            currency=contract.currency,
            notionalPrincipal=contract.principal,
            nominalInterestRate=nominal_interest_rate,
            initialExchangeDate=initial_exchange_date_str,
            maturityDate=maturity_date_str,
            statusDate=status_date_str,
            cycleOfInterestPayment=interest_cycle,
            cycleAnchorDateOfInterestPayment=initial_exchange_date_str,
            cycleOfPrincipalRedemption=principal_cycle,
            cycleAnchorDateOfPrincipalRedemption=initial_exchange_date_str if principal_cycle else None,
            dayCountConvention=day_count_convention,
            interestCalculationBase=None,
        )

        # 5. ACTUS Specific Validation Layer
        validation_valid, validation_msg = cls._validate_actus_contract(actus_contract, contract)
        if not validation_valid:
            warnings.append(validation_msg)
            return ActusMappingRecord(
                source_contract_id=contract.contract_id,
                mapping_status=ActusMappingStatus.INVALID,
                actus_contract=actus_contract,
                warnings=warnings,
                missing_attributes=missing_attributes,
                created_at=datetime.now(timezone.utc),
            )

        # Determine final mapping status
        if missing_attributes or not contract_type:
            mapping_status = ActusMappingStatus.REQUIRES_REVIEW
        else:
            mapping_status = ActusMappingStatus.MAPPED

        return ActusMappingRecord(
            source_contract_id=contract.contract_id,
            mapping_status=mapping_status,
            actus_contract=actus_contract,
            warnings=warnings,
            missing_attributes=missing_attributes,
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _classify_contract_type(contract: FinancialContract) -> Tuple[Optional[str], Optional[str]]:
        """Determine ACTUS contractType based on explicit contractual information."""
        desc = (contract.description or "").lower()

        if any(term in desc for term in ["annuity", "amortizing loan", "fixed periodic total", "fixed-rate amortizing"]):
            return "ANN", None

        if any(term in desc for term in ["bullet", "principal at maturity", "interest-only", "pam"]):
            return "PAM", None

        if any(term in desc for term in ["linear amortizing", "linear principal", "lam"]):
            return "LAM", None

        # If repayment structure is ambiguous/unspecified, DO NOT guess
        return None, "Repayment structure is insufficient to determine ACTUS contractType without human review."

    @staticmethod
    def _validate_actus_contract(actus: ActusContract, source: FinancialContract) -> Tuple[bool, str]:
        """Perform additional ACTUS-specific validation rules."""
        if actus.notionalPrincipal <= Decimal("0"):
            return False, "ACTUS validation failed: notionalPrincipal must be strictly positive."

        if actus.nominalInterestRate < Decimal("0"):
            return False, "ACTUS validation failed: nominalInterestRate cannot be negative."

        if source.start_date >= source.maturity_date:
            return False, "ACTUS validation failed: initialExchangeDate must be before maturityDate."

        return True, ""
