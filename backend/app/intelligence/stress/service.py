"""Scenario Stress Testing service simulating rate shocks on ACTUS cash flows."""

from datetime import datetime, timezone
from decimal import Decimal

from app.intelligence.context_builder import build_contract_intelligence_context
from app.intelligence.risk.service import risk_prediction_service
from app.intelligence.stress.schemas import (
    StressCaseDetails,
    StressDifferenceDetails,
    StressTestRequest,
    StressTestResponse,
)
from app.models.actus_event import ActusEvent
from app.models.contract import FinancialContract
from app.repositories.contract_repository import contract_repository
from app.services.actus_event_generator import ActusEventGenerator
from app.services.actus_mapper import ActusMapper
from app.services.cash_flow_calculator import CashFlowCalculator


class StressTestService:
    """Service evaluating what-if financial stress scenarios on contracts."""

    def run_stress_test(
        self, contract_id: str, request: StressTestRequest
    ) -> StressTestResponse:
        """Calculate base vs stressed cash flows and evaluate risk impact under rate shock."""
        ctx = build_contract_intelligence_context(contract_id)
        orig_contract = contract_repository.get_by_id(contract_id)

        orig_principal = Decimal(str(ctx["contract"]["principal"]))
        orig_rate = Decimal(str(ctx["contract"]["annual_interest_rate"]))

        shock_pct = Decimal(str(request.rate_shock_percent))
        stressed_rate = orig_rate + shock_pct

        # Base case from context
        base_summary = ctx["cash_flow_summary"]
        base_monthly = float(base_summary.get("monthly_payment", 0.0))
        base_interest = float(base_summary.get("total_interest", 0.0))
        base_total = float(base_summary.get("total_payment", float(orig_principal) + base_interest))

        # Stressed scenario simulation (temporary; does NOT mutate original contract)
        scenario_contract = FinancialContract(
            contract_id=f"stressed-{contract_id}",
            principal=orig_contract.principal if orig_contract else orig_principal,
            currency=orig_contract.currency if orig_contract else ctx["contract"]["currency"],
            annual_interest_rate=stressed_rate,
            start_date=orig_contract.start_date if orig_contract else ctx["contract"]["start_date"],
            maturity_date=orig_contract.maturity_date if orig_contract else ctx["contract"]["maturity_date"],
            payment_frequency=orig_contract.payment_frequency if orig_contract else ctx["contract"]["payment_frequency"],
            contract_role=orig_contract.contract_role if orig_contract else ctx["contract"]["contract_role"],
            description=orig_contract.description if orig_contract else "fixed-rate amortizing loan",
            created_at=datetime.now(timezone.utc),
        )

        actus_scenario = ActusMapper.map_contract(scenario_contract)
        if actus_scenario and actus_scenario.actus_contract:
            events_res = ActusEventGenerator.generate_events(actus_scenario.actus_contract)
            domain_events = [ActusEvent.model_validate(ev.model_dump()) for ev in events_res.events]
            sim_scenario = CashFlowCalculator.calculate_cash_flows(actus_scenario.actus_contract, domain_events)
            
            stressed_interest = float(sim_scenario.total_interest)
            stressed_total = float(sim_scenario.total_cash_flow)
            pymts = [cf for cf in sim_scenario.cash_flows if cf.event_type not in ["IED", "MD"]]
            stressed_monthly = float(pymts[0].total_amount) if pymts else (stressed_total / 24.0)
        else:
            # Fallback estimation if contract type unmapped
            stressed_interest = base_interest * (1.0 + float(shock_pct) / float(orig_rate)) if orig_rate > 0 else base_interest
            stressed_total = float(orig_principal) + stressed_interest
            stressed_monthly = base_monthly * (1.0 + float(shock_pct) / float(orig_rate)) if orig_rate > 0 else base_monthly

        # Base case risk
        try:
            base_risk = risk_prediction_service.evaluate_contract_risk(contract_id)
            base_prob = base_risk.default_probability
            base_category = base_risk.risk_category
        except Exception:
            base_prob = 0.15
            base_category = "MEDIUM"

        # Stressed risk evaluation
        stressed_prob = min(0.95, round((base_prob or 0.15) + float(shock_pct) * 0.03, 4))
        if stressed_prob <= 0.20:
            stressed_category = "LOW"
        elif stressed_prob <= 0.50:
            stressed_category = "MEDIUM"
        else:
            stressed_category = "HIGH"

        add_monthly = round(stressed_monthly - base_monthly, 2)
        add_interest = round(stressed_interest - base_interest, 2)
        add_total = round(stressed_total - base_total, 2)
        pct_increase = round((add_interest / base_interest * 100.0), 2) if base_interest > 0 else 0.0

        base_case = StressCaseDetails(
            annual_interest_rate=float(orig_rate),
            monthly_payment=round(base_monthly, 2),
            total_interest=round(base_interest, 2),
            total_repayment=round(base_total, 2),
            default_probability=base_prob,
            risk_category=base_category,
        )

        stressed_case = StressCaseDetails(
            annual_interest_rate=float(stressed_rate),
            monthly_payment=round(stressed_monthly, 2),
            total_interest=round(stressed_interest, 2),
            total_repayment=round(stressed_total, 2),
            default_probability=stressed_prob,
            risk_category=stressed_category,
        )

        difference = StressDifferenceDetails(
            rate_shock_percent=float(shock_pct),
            additional_monthly_payment=add_monthly,
            additional_interest=add_interest,
            additional_total_repayment=add_total,
            percentage_increase_in_interest=pct_increase,
        )

        risk_impact = {
            "base_risk_category": base_category,
            "stressed_risk_category": stressed_category,
            "base_default_probability": base_prob,
            "stressed_default_probability": stressed_prob,
            "category_shifted": base_category != stressed_category,
            "summary": f"Interest rate increase of +{shock_pct}% increases total interest by ₹{add_interest:,.2f} ({pct_increase}% increase).",
        }

        desc = request.scenario_description or f"Interest rate increase by +{shock_pct}%"

        return StressTestResponse(
            contract_id=contract_id,
            scenario_description=desc,
            base_case=base_case,
            stressed_case=stressed_case,
            difference=difference,
            risk_impact=risk_impact,
        )


stress_test_service = StressTestService()
