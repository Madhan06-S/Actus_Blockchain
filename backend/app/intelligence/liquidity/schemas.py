"""Pydantic schemas for Portfolio Liquidity Engine."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class LiquidityForecastRequest(BaseModel):
    """Request schema for portfolio liquidity forecasting."""
    contract_ids: Optional[List[str]] = Field(None, description="List of contract IDs to include; defaults to all active contracts")
    bank_outflows_by_year: Optional[Dict[str, float]] = Field(
        default_factory=lambda: {"2027": 50000.0, "2028": 60000.0, "2029": 70000.0},
        description="Configured bank obligations by year string (e.g. {'2027': 5000000})"
    )


class YearlyLiquidityItem(BaseModel):
    """Liquidity breakdown for a single calendar year."""
    year: str = Field(..., description="Calendar year (YYYY)")
    portfolio_inflow: float = Field(..., description="Total expected positive cash flows for this year")
    bank_outflow: float = Field(..., description="Configured bank outflow obligations")
    net_liquidity: float = Field(..., description="Net liquidity (inflow - outflow)")
    status: str = Field(..., description="Status: SAFE or DEFICIT_RISK")


class LiquidityForecastResponse(BaseModel):
    """Response schema for portfolio liquidity forecasting."""
    forecast: Dict[str, YearlyLiquidityItem] = Field(..., description="Year-by-year liquidity breakdown")
    overall_status: str = Field(..., description="Overall portfolio status: SAFE or DEFICIT_RISK")
    total_inflow: float = Field(..., description="Total cumulative expected inflows across forecast period")
    total_outflow: float = Field(..., description="Total cumulative outflows across forecast period")
    contract_count: int = Field(..., description="Number of contracts included in forecast")
