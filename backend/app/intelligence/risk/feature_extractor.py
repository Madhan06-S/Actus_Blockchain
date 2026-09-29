"""Feature extraction logic for contract risk prediction."""

from datetime import datetime
from typing import Any, Dict, List, Tuple


def _calculate_months(start_str: str, maturity_str: str) -> int:
    """Calculate duration in months between start date and maturity date."""
    try:
        dt1 = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        dt2 = datetime.fromisoformat(maturity_str.replace("Z", "+00:00"))
        return max(1, (dt2.year - dt1.year) * 12 + (dt2.month - dt1.month))
    except Exception:
        return 24


class FeatureExtractor:
    """Extract 22+ quantitative features from normalized contract intelligence context."""

    @classmethod
    def extract_features(cls, ctx: Dict[str, Any]) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
        contract = ctx.get("contract", {})
        actus = ctx.get("actus", {})
        cash_flows = ctx.get("cash_flows", [])
        cf_summary = ctx.get("cash_flow_summary", {})
        recon = ctx.get("reconciliation", {})

        principal = float(contract.get("principal", 0.0))
        annual_rate = float(contract.get("annual_interest_rate", 0.0))
        nominal_rate = float(actus.get("nominal_interest_rate", annual_rate / 100.0))
        duration_months = _calculate_months(contract.get("start_date", ""), contract.get("maturity_date", ""))
        expected_payments = cf_summary.get("payment_count", len(cash_flows))
        
        total_interest = cf_summary.get("total_interest", 0.0)
        total_repayment = cf_summary.get("total_payment", principal + total_interest)
        
        interest_to_principal = (total_interest / principal) if principal > 0 else 0.0
        avg_payment = (total_repayment / expected_payments) if expected_payments > 0 else 0.0
        
        amounts = [cf.get("amount", 0.0) for cf in cash_flows] if cash_flows else [avg_payment]
        max_payment = max(amounts) if amounts else avg_payment
        min_payment = min(amounts) if amounts else avg_payment
        
        payment_to_principal = (avg_payment / principal) if principal > 0 else 0.0
        
        # Event count proxies
        ip_count = expected_payments
        pr_count = 1 if actus.get("contract_type") == "PAM" else expected_payments
        md_count = 1
        total_actus_events = ip_count + pr_count + md_count + 1  # includes IED

        actual_paid = float(recon.get("actual_total", 0.0))
        expected_total = float(recon.get("expected_total", total_repayment))
        recon_diff = float(recon.get("net_variance", actual_paid - expected_total))
        actual_to_expected = (actual_paid / expected_total) if expected_total > 0 else 0.0
        
        unpaid_count = recon.get("unpaid_payment_count", 0)
        overdue_count = recon.get("overdue_payment_count", 0)
        remaining_count = unpaid_count + overdue_count

        features_dict = {
            "principal": principal,
            "annual_interest_rate": annual_rate,
            "nominal_interest_rate": nominal_rate,
            "loan_duration_months": float(duration_months),
            "expected_payment_count": float(expected_payments),
            "payment_frequency_monthly": 1.0 if contract.get("payment_frequency") == "MONTHLY" else 0.0,
            "total_interest": total_interest,
            "total_repayment": total_repayment,
            "interest_to_principal_ratio": interest_to_principal,
            "average_payment": avg_payment,
            "maximum_payment": max_payment,
            "minimum_payment": min_payment,
            "payment_to_principal_ratio": payment_to_principal,
            "actus_event_count": float(total_actus_events),
            "ip_event_count": float(ip_count),
            "pr_event_count": float(pr_count),
            "md_event_count": float(md_count),
            "remaining_payment_count": float(remaining_count),
            "reconciliation_difference": recon_diff,
            "actual_to_expected_ratio": actual_to_expected,
            "unpaid_payment_count": float(unpaid_count),
            "overdue_payment_count": float(overdue_count),
        }

        metadata_list = [
            {"name": "principal", "value": principal, "description": "Loan principal amount"},
            {"name": "annual_interest_rate", "value": annual_rate, "description": "Annual interest rate (%)"},
            {"name": "loan_duration_months", "value": duration_months, "description": "Contract duration in months"},
            {"name": "expected_payment_count", "value": expected_payments, "description": "Total scheduled payment events"},
            {"name": "total_interest", "value": round(total_interest, 2), "description": "Total interest over loan lifetime"},
            {"name": "total_repayment", "value": round(total_repayment, 2), "description": "Total principal + interest repayment"},
            {"name": "interest_to_principal_ratio", "value": round(interest_to_principal, 4), "description": "Ratio of total interest to principal"},
            {"name": "average_payment", "value": round(avg_payment, 2), "description": "Average monthly payment amount"},
            {"name": "overdue_payment_count", "value": overdue_count, "description": "Count of overdue scheduled payments"},
            {"name": "reconciliation_difference", "value": round(recon_diff, 2), "description": "Net difference between actual paid and expected"},
        ]

        return features_dict, metadata_list
