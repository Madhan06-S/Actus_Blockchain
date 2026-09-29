"""
Currency conversion service — converts any supported currency to INR.

Exchange rates are static approximations (Sep 2024 reference rates).
For production use, replace _RATES with a live-feed integration.
"""

from __future__ import annotations

from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Static exchange rates  →  1 unit of foreign currency = X INR
# Update these periodically or swap for a live-rate API call.
# ──────────────────────────────────────────────────────────────────────────────
_RATES_TO_INR: dict[str, float] = {
    "INR": 1.0,
    "USD": 84.0,       # 1 USD ≈ ₹84
    "EUR": 91.0,       # 1 EUR ≈ ₹91
    "GBP": 106.0,      # 1 GBP ≈ ₹106
    "JPY": 0.57,       # 1 JPY ≈ ₹0.57
    "SGD": 63.0,       # 1 SGD ≈ ₹63
    "AUD": 55.0,       # 1 AUD ≈ ₹55
    "CAD": 61.0,       # 1 CAD ≈ ₹61
    "CHF": 95.0,       # 1 CHF ≈ ₹95
    "CNY": 11.6,       # 1 CNY ≈ ₹11.6
    "AED": 22.9,       # 1 AED ≈ ₹22.9
}


class CurrencyConverter:
    """Convert financial amounts between currencies using static INR reference rates."""

    @classmethod
    def get_rate_to_inr(cls, currency: str) -> Optional[float]:
        """Return the INR equivalent of 1 unit of `currency`. None if unknown."""
        return _RATES_TO_INR.get(currency.upper())

    @classmethod
    def to_inr(cls, amount: float, from_currency: str) -> tuple[float, float]:
        """
        Convert `amount` in `from_currency` to INR.

        Returns:
            (inr_amount, rate_used)  —  rate_used is INR per 1 unit of from_currency.

        Raises:
            ValueError: if the currency code is not in the rate table.
        """
        currency_upper = from_currency.upper()
        rate = _RATES_TO_INR.get(currency_upper)
        if rate is None:
            raise ValueError(
                f"No INR conversion rate for currency '{from_currency}'. "
                f"Supported: {', '.join(sorted(_RATES_TO_INR))}"
            )
        inr_amount = amount * rate
        return inr_amount, rate

    @classmethod
    def format_conversion_note(cls, original_amount: float, original_currency: str, inr_amount: float, rate: float) -> str:
        """Return a human-readable conversion note like 'USD 200,000,000 @ ₹84/USD → ₹16,80,00,00,000'."""
        orig_fmt = f"{original_currency} {original_amount:,.2f}"
        inr_fmt  = f"₹{inr_amount:,.2f}"
        return f"{orig_fmt} @ ₹{rate}/{original_currency} → {inr_fmt}"

    @classmethod
    def is_supported(cls, currency: str) -> bool:
        return currency.upper() in _RATES_TO_INR
