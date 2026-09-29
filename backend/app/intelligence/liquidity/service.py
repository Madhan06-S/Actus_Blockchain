"""Liquidity Engine service calculating portfolio cash inflows vs bank outflows."""

from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional

from app.intelligence.context_builder import build_contract_intelligence_context
from app.intelligence.liquidity.schemas import (
    LiquidityForecastRequest,
    LiquidityForecastResponse,
    YearlyLiquidityItem,
)
from app.repositories.contract_repository import contract_repository


class LiquidityService:
    """Portfolio liquidity forecast calculator."""

    def forecast_portfolio_liquidity(
        self, request: Optional[LiquidityForecastRequest] = None
    ) -> LiquidityForecastResponse:
        """Forecast portfolio net liquidity by aggregating cash flows across contracts and comparing with bank outflows."""
        if request is None:
            request = LiquidityForecastRequest()

        target_ids = request.contract_ids
        if not target_ids:
            all_contracts = contract_repository.get_all()
            target_ids = [c.contract_id for c in all_contracts]

        configured_outflows = request.bank_outflows_by_year or {
            "2027": 50000.0,
            "2028": 60000.0,
            "2029": 70000.0,
        }

        yearly_inflows: Dict[str, Decimal] = defaultdict(Decimal)

        included_contract_count = 0
        for cid in target_ids:
            try:
                ctx = build_contract_intelligence_context(cid)
                cash_flows = ctx.get("cash_flows", [])
                included_contract_count += 1
                for cf in cash_flows:
                    date_str = cf.get("date", "")
                    amount = Decimal(str(cf.get("amount", 0.0)))
                    if date_str and amount > Decimal("0"):
                        year = date_str.split("-")[0]
                        yearly_inflows[year] += amount
            except Exception:
                continue

        all_years = sorted(list(set(list(yearly_inflows.keys()) + list(configured_outflows.keys()))))
        if not all_years:
            all_years = ["2027", "2028", "2029"]

        forecast_map: Dict[str, YearlyLiquidityItem] = {}
        has_deficit = False
        cum_inflow = Decimal("0")
        cum_outflow = Decimal("0")

        for yr in all_years:
            inflow = yearly_inflows.get(yr, Decimal("0"))
            outflow = Decimal(str(configured_outflows.get(yr, 0.0)))
            net = inflow - outflow

            cum_inflow += inflow
            cum_outflow += outflow

            status_str = "SAFE" if net >= Decimal("0") else "DEFICIT_RISK"
            if status_str == "DEFICIT_RISK":
                has_deficit = True

            forecast_map[yr] = YearlyLiquidityItem(
                year=yr,
                portfolio_inflow=float(inflow),
                bank_outflow=float(outflow),
                net_liquidity=float(net),
                status=status_str,
            )

        overall = "DEFICIT_RISK" if has_deficit else "SAFE"

        return LiquidityForecastResponse(
            forecast=forecast_map,
            overall_status=overall,
            total_inflow=float(cum_inflow),
            total_outflow=float(cum_outflow),
            contract_count=included_contract_count,
        )


liquidity_service = LiquidityService()
