"""Shared context builder for financial intelligence engines."""

from decimal import Decimal
from typing import Any, Dict
from fastapi import HTTPException, status

from app.repositories.actus_event_repository import actus_event_repository
from app.repositories.actus_repository import actus_repository
from app.repositories.cash_flow_repository import cash_flow_repository
from app.repositories.contract_repository import contract_repository
from app.services.actus_event_service import actus_event_service
from app.services.actus_mapper import ActusMapper
from app.services.cash_flow_service import cash_flow_service
from app.services.risk_status_service import risk_status_service


def build_contract_intelligence_context(contract_id: str) -> Dict[str, Any]:
    """Gather normalized contract, ACTUS mapping, cash flows, and reconciliation data.
    
    Reuses existing Phase 1-8 domain services and repositories without duplicating calculations.
    """
    contract = contract_repository.get_by_id(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID '{contract_id}' not found.",
        )

    # 1. Ensure ACTUS contract mapping exists
    actus_rec = actus_repository.get_by_source_id(contract_id)
    if not actus_rec:
        actus_rec = ActusMapper.map_contract(contract)
        actus_repository.save(actus_rec)

    # 2. Ensure ACTUS event timeline exists
    event_rec = actus_event_repository.get_by_contract_id(contract_id)
    if not event_rec:
        try:
            event_rec = actus_event_service.generate_events_for_contract(contract_id)
        except Exception:
            event_rec = None

    # 3. Ensure cash flow simulation exists
    sim_result = cash_flow_repository.get_by_contract_id(contract_id)
    if not sim_result:
        try:
            sim_result = cash_flow_service.calculate_cash_flows(contract_id)
        except Exception:
            sim_result = None

    # 4. Gather reconciliation indicators
    try:
        recon_status = risk_status_service.calculate_risk_status(contract_id)
        recon_dict = {
            "overall_status": recon_status.overall_status.value if hasattr(recon_status.overall_status, "value") else str(recon_status.overall_status),
            "expected_total": float(recon_status.total_expected_amount),
            "actual_total": float(recon_status.total_actual_paid),
            "net_variance": float(recon_status.net_amount_variance),
            "expected_payment_count": recon_status.total_expected_payments,
            "actual_payment_count": recon_status.matched_payment_count,
            "unpaid_payment_count": recon_status.unpaid_payment_count,
            "overdue_payment_count": recon_status.overdue_payment_count,
            "unexpected_payment_count": recon_status.unexpected_payment_count,
            "hash_integrity_matched": recon_status.hash_integrity_matched,
            "blockchain_status": recon_status.blockchain_status.value if recon_status.blockchain_status else "UNKNOWN",
            "blockchain_address": recon_status.blockchain_contract_address,
            "status_reasons": recon_status.status_reasons,
        }
    except Exception:
        exp_total = float(sim_result.total_cash_flow) if sim_result else float(contract.principal)
        exp_count = len(sim_result.cash_flows) if sim_result else 24
        recon_dict = {
            "overall_status": "NOT_EVALUATED",
            "expected_total": exp_total,
            "actual_total": 0.0,
            "net_variance": -exp_total,
            "expected_payment_count": exp_count,
            "actual_payment_count": 0,
            "unpaid_payment_count": exp_count,
            "overdue_payment_count": 0,
            "unexpected_payment_count": 0,
            "hash_integrity_matched": False,
            "blockchain_status": "NONE",
            "blockchain_address": None,
            "status_reasons": ["Reconciliation not yet calculated."],
        }

    formatted_cash_flows = []
    total_interest = 0.0
    total_payment = float(contract.principal)
    monthly_payment = 0.0

    if sim_result:
        total_interest = float(sim_result.total_interest)
        total_payment = float(sim_result.total_cash_flow)
        
        # Payment events
        pymt_cfs = [cf for cf in sim_result.cash_flows if cf.event_type not in ["IED", "MD"]]
        monthly_payment = float(pymt_cfs[0].total_amount) if pymt_cfs else (total_payment / 24.0)

        for idx, cf in enumerate(sim_result.cash_flows, start=1):
            formatted_cash_flows.append(
                {
                    "payment_number": idx,
                    "event_type": cf.event_type,
                    "date": cf.event_time,
                    "amount": float(cf.total_amount),
                    "principal_payment": float(cf.principal_amount),
                    "interest_payment": float(cf.interest_amount),
                    "remaining_principal": float(cf.closing_principal),
                }
            )

    return {
        "contract": {
            "contract_id": contract.contract_id,
            "principal": float(contract.principal),
            "currency": contract.currency,
            "annual_interest_rate": float(contract.annual_interest_rate),
            "start_date": contract.start_date.isoformat(),
            "maturity_date": contract.maturity_date.isoformat(),
            "payment_frequency": contract.payment_frequency.value if hasattr(contract.payment_frequency, "value") else str(contract.payment_frequency),
            "contract_role": contract.contract_role.value if hasattr(contract.contract_role, "value") else str(contract.contract_role),
            "description": contract.description or "",
        },
        "actus": {
            "contract_type": actus_rec.actus_contract.contractType if actus_rec and actus_rec.actus_contract else None,
            "nominal_interest_rate": float(actus_rec.actus_contract.nominalInterestRate) if actus_rec and actus_rec.actus_contract and actus_rec.actus_contract.nominalInterestRate is not None else float(contract.annual_interest_rate / Decimal("100")),
            "mapping_status": actus_rec.mapping_status.value if actus_rec else "UNMAPPED",
        },
        "cash_flows": formatted_cash_flows,
        "cash_flow_summary": {
            "total_interest": total_interest,
            "total_payment": total_payment,
            "payment_count": len(formatted_cash_flows) or 24,
            "monthly_payment": monthly_payment,
        },
        "reconciliation": recon_dict,
    }
