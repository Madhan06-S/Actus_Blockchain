"""Service for extracting candidate financial contract terms from raw text using rule-based pattern matching."""

from datetime import datetime
import re
from typing import Dict, List, Optional, Tuple

from app.models.document import ConfidenceLevel
from app.schemas.document import ExtractedTermsResponse, FieldExtractionResult


def normalize_date_string(date_str: str) -> Optional[str]:
    """Parse date strings like 'January 1, 2027' or '2027-01-01' into 'YYYY-MM-DD'."""
    cleaned = date_str.strip()

    # Check for date format ambiguity between %m/%d/%Y and %d/%m/%Y
    try:
        dt_m = datetime.strptime(cleaned, "%m/%d/%Y")
        dt_d = datetime.strptime(cleaned, "%d/%m/%Y")
        if dt_m.date() != dt_d.date():
            return None
    except ValueError:
        pass

    formats = [
        "%B %d, %Y",     # January 1, 2027
        "%B %d %Y",      # January 1 2027
        "%b %d, %Y",     # Jan 1, 2027
        "%Y-%m-%d",      # 2027-01-01
        "%d-%m-%Y",      # 01-01-2027
        "%m/%d/%Y",      # 01/01/2027
        "%d/%m/%Y",      # 01/01/2027
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


# Multiplier words for large number expansion (e.g. "200 million" -> 200_000_000)
_WORD_MULTIPLIERS = {
    "hundred": 100,
    "thousand": 1_000,
    "lakh": 1_00_000,
    "lac": 1_00_000,
    "million": 1_000_000,
    "crore": 1_00_00_000,
    "billion": 1_000_000_000,
}


def _expand_word_amount(text: str) -> Optional[float]:
    """
    Try to parse a human-readable amount like '200 million', '1.5 crore', '2,00,000'.
    Returns float or None.
    """
    text = text.strip().lower()
    # Remove commas (Indian / international formatting)
    text_no_comma = text.replace(",", "")
    # Try plain numeric first
    try:
        return float(text_no_comma)
    except ValueError:
        pass

    # Try "<number> <multiplier>"
    m = re.match(r"([\d,]+(?:\.\d+)?)\s+(" + "|".join(_WORD_MULTIPLIERS.keys()) + r")", text)
    if m:
        base = float(m.group(1).replace(",", ""))
        mult = _WORD_MULTIPLIERS[m.group(2)]
        return base * mult

    return None


class ContractTermExtractor:
    """Rule-based extractor for candidate financial terms from document text."""

    REQUIRED_FIELDS = [
        "principal",
        "currency",
        "annual_interest_rate",
        "start_date",
        "maturity_date",
        "payment_frequency",
    ]

    @classmethod
    def extract_terms(cls, text: str, document_id: str) -> ExtractedTermsResponse:
        """Extract candidate contract terms from raw text."""
        fields: Dict[str, FieldExtractionResult] = {}
        missing_fields: List[str] = []
        warnings: List[str] = []

        if not text or not text.strip():
            warnings.append("Document contains no text for extraction.")
            for field in cls.REQUIRED_FIELDS:
                fields[field] = FieldExtractionResult(
                    value=None,
                    confidence=ConfidenceLevel.NOT_FOUND,
                    source=None,
                )
                missing_fields.append(field)
            return ExtractedTermsResponse(
                document_id=document_id,
                status="TEXT_NOT_EXTRACTABLE",
                fields=fields,
                missing_fields=missing_fields,
                warnings=warnings,
            )

        # 1. Currency Extraction  — must run BEFORE principal so we can cross-check
        curr_val, curr_conf, curr_src = cls._extract_currency(text)
        if curr_val:
            fields["currency"] = FieldExtractionResult(value=curr_val, confidence=curr_conf, source=curr_src)
        else:
            fields["currency"] = FieldExtractionResult(value=None, confidence=ConfidenceLevel.NOT_FOUND, source=None)
            missing_fields.append("currency")

        # 2. Principal Extraction — use detected currency to guide extraction
        detected_currency = curr_val  # may be None
        p_val, p_conf, p_src = cls._extract_principal(text, detected_currency)
        if p_val:
            fields["principal"] = FieldExtractionResult(value=p_val, confidence=p_conf, source=p_src)
        else:
            fields["principal"] = FieldExtractionResult(value=None, confidence=ConfidenceLevel.NOT_FOUND, source=None)
            missing_fields.append("principal")

        # 3. Annual Interest Rate Extraction
        r_val, r_conf, r_src = cls._extract_interest_rate(text)
        if r_val:
            fields["annual_interest_rate"] = FieldExtractionResult(value=r_val, confidence=r_conf, source=r_src)
        else:
            fields["annual_interest_rate"] = FieldExtractionResult(value=None, confidence=ConfidenceLevel.NOT_FOUND, source=None)
            missing_fields.append("annual_interest_rate")

        # 4. Start Date Extraction
        s_val, s_conf, s_src = cls._extract_start_date(text)
        if s_val:
            fields["start_date"] = FieldExtractionResult(value=s_val, confidence=s_conf, source=s_src)
        else:
            fields["start_date"] = FieldExtractionResult(value=None, confidence=ConfidenceLevel.NOT_FOUND, source=None)
            missing_fields.append("start_date")

        # 5. Maturity Date Extraction
        m_val, m_conf, m_src = cls._extract_maturity_date(text)
        if m_val:
            fields["maturity_date"] = FieldExtractionResult(value=m_val, confidence=m_conf, source=m_src)
        else:
            fields["maturity_date"] = FieldExtractionResult(value=None, confidence=ConfidenceLevel.NOT_FOUND, source=None)
            missing_fields.append("maturity_date")

        # 6. Payment Frequency Extraction
        f_val, f_conf, f_src = cls._extract_payment_frequency(text)
        if f_val:
            fields["payment_frequency"] = FieldExtractionResult(value=f_val, confidence=f_conf, source=f_src)
        else:
            fields["payment_frequency"] = FieldExtractionResult(value=None, confidence=ConfidenceLevel.NOT_FOUND, source=None)
            missing_fields.append("payment_frequency")

        if missing_fields:
            warnings.append(f"Missing required fields: {', '.join(missing_fields)}")

        return ExtractedTermsResponse(
            document_id=document_id,
            status="TEXT_EXTRACTED",
            fields=fields,
            missing_fields=missing_fields,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Currency detection — ordered to avoid false-positive INR when USD
    # text is dominant.
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_currency(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        """
        Detect the *dominant* currency in the document text.
        We score each currency by the number of occurrences and pick the winner.
        This prevents a single stray "INR" mention from masking a USD contract.
        """
        scores: Dict[str, int] = {"INR": 0, "USD": 0, "EUR": 0, "GBP": 0}

        # INR markers
        scores["INR"] += len(re.findall(r"₹", text))
        scores["INR"] += len(re.findall(r"\b(?:INR|Rs\.?|Rupees?)\b", text, re.IGNORECASE))

        # USD markers
        scores["USD"] += len(re.findall(r"\$", text))
        scores["USD"] += len(re.findall(r"\bUSD\b", text, re.IGNORECASE))
        scores["USD"] += len(re.findall(r"\bUS\s+Dollars?\b", text, re.IGNORECASE))

        # EUR markers
        scores["EUR"] += len(re.findall(r"€", text))
        scores["EUR"] += len(re.findall(r"\bEUR\b", text, re.IGNORECASE))
        scores["EUR"] += len(re.findall(r"\bEuros?\b", text, re.IGNORECASE))

        # GBP markers
        scores["GBP"] += len(re.findall(r"£", text))
        scores["GBP"] += len(re.findall(r"\bGBP\b", text, re.IGNORECASE))
        scores["GBP"] += len(re.findall(r"\bPounds?\b", text, re.IGNORECASE))

        # Pick the currency with the highest score
        best = max(scores, key=lambda k: scores[k])
        if scores[best] > 0:
            conf = ConfidenceLevel.HIGH if scores[best] >= 2 else ConfidenceLevel.MEDIUM
            return best, conf, best
        return None, ConfidenceLevel.NOT_FOUND, None

    # ------------------------------------------------------------------
    # Principal extraction — handles large numbers & word multipliers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_principal(text: str, currency: Optional[str] = None) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        """
        Extract the loan/contract principal amount.
        Handles:
          - Standard numeric: ₹1,00,000 / $200,000,000 / INR 50000
          - Word multipliers: USD 200 million / 1.5 crore
          - Labelled patterns: principal amount, loan amount, Section 2.01, etc.
        """

        # Build a generic currency symbol pattern depending on detected currency
        _sym = {
            "INR": r"(?:INR|₹|Rs\.?|Rupees?)",
            "USD": r"(?:USD|\$|US\s+Dollars?)",
            "EUR": r"(?:EUR|€|Euros?)",
            "GBP": r"(?:GBP|£|Pounds?)",
        }
        sym_pat = _sym.get(currency or "", r"(?:INR|USD|EUR|GBP|₹|Rs\.?|\$|€|£)")

        candidates: List[Tuple[float, str, ConfidenceLevel]] = []

        def _add(raw_text: str, label: str, conf: ConfidenceLevel) -> None:
            val = _expand_word_amount(raw_text)
            if val is not None and val > 0:
                candidates.append((val, label, conf))

        # ---- Pattern 1: labelled principal/loan amount with optional currency symbol ----
        # e.g. "Principal Amount: $200,000,000" / "loan amount of USD 200 million"
        p1 = re.compile(
            r"(?:principal(?:\s+amount)?|loan\s+amount(?:\s+of)?|loan\s+of|sum\s+of|total\s+loan|amount\s+of\s+loan)"
            r"[\s\S]{0,40}?"               # allow up to 40 chars of non-greedy filler (Article refs etc)
            r"(?:" + sym_pat + r")?\s*"
            r"([\d,]+(?:\.\d+)?)"
            r"(?:\s+(" + "|".join(_WORD_MULTIPLIERS.keys()) + r"))?",
            re.IGNORECASE
        )
        for m in p1.finditer(text):
            raw = m.group(1)
            multiplier_word = m.group(2) or ""
            full = raw + (" " + multiplier_word if multiplier_word else "")
            _add(full, m.group(0)[:80], ConfidenceLevel.HIGH)

        # ---- Pattern 2: currency-prefixed number (with optional word multiplier) ----
        # e.g. "$200,000,000" / "USD 200 million" / "₹1,00,000"
        p2 = re.compile(
            sym_pat + r"\s*([\d,]+(?:\.\d+)?)"
            r"(?:\s+(" + "|".join(_WORD_MULTIPLIERS.keys()) + r"))?",
            re.IGNORECASE
        )
        for m in p2.finditer(text):
            raw = m.group(1)
            multiplier_word = m.group(2) or ""
            full = raw + (" " + multiplier_word if multiplier_word else "")
            _add(full, m.group(0)[:60], ConfidenceLevel.MEDIUM)

        # ---- Pattern 3: number-suffixed currency ----
        # e.g. "200000 USD" / "50000 Rupees"
        p3 = re.compile(
            r"([\d,]+(?:\.\d+)?)\s*" + sym_pat,
            re.IGNORECASE
        )
        for m in p3.finditer(text):
            _add(m.group(1), m.group(0)[:60], ConfidenceLevel.MEDIUM)

        # ---- Pattern 4: "amount / value / borrowed" label ----
        p4 = re.compile(
            r"(?:amount|value|borrowed)\s*:?\s*[^\d\s]*\s*([\d,]+(?:\.\d+)?)",
            re.IGNORECASE
        )
        for m in p4.finditer(text):
            _add(m.group(1), m.group(0)[:60], ConfidenceLevel.MEDIUM)

        if not candidates:
            return None, ConfidenceLevel.NOT_FOUND, None

        # Prefer HIGH confidence; among same confidence take the largest amount
        high = [(v, s, c) for (v, s, c) in candidates if c == ConfidenceLevel.HIGH]
        if high:
            best = max(high, key=lambda x: x[0])
        else:
            best = max(candidates, key=lambda x: x[0])

        # Return as integer string when there's no fractional part (100000.0 → "100000")
        val = best[0]
        val_str = str(int(val)) if val == int(val) else str(val)
        return val_str, best[2], best[1]

    @staticmethod
    def _extract_interest_rate(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        # Pattern 1: "annual interest rate: 10%" or "interest rate: 10% per annum" or "rate: 12%"
        pattern1 = r"(?:annual\s+)?interest(?:\s+rate)?\s*:?\s*([\d.]+)\s*(?:%|percent)?"
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1), ConfidenceLevel.HIGH, match.group(0)

        # Pattern 2: "10% per annum", "10 percent annual interest", "@ 12%"
        pattern2 = r"(?:@\s*)?([\d.]+)\s*(?:%|percent)\s*(?:per\s+annum|annual|p\.a\.)?(?:\s+interest)?"
        match2 = re.search(pattern2, text, re.IGNORECASE)
        if match2:
            return match2.group(1), ConfidenceLevel.HIGH, match2.group(0)

        # Pattern 3: front-end fee / service charge (fallback)
        pattern3 = r"(?:front[- ]end\s+fee|service\s+charge|commitment\s+fee)\s*:?\s*([\d.]+)\s*(?:%|percent)"
        match3 = re.search(pattern3, text, re.IGNORECASE)
        if match3:
            return match3.group(1), ConfidenceLevel.MEDIUM, match3.group(0)

        return None, ConfidenceLevel.NOT_FOUND, None

    @staticmethod
    def _extract_start_date(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        pattern = r"(?:start|commencement|inception|effective|disbursement)\s+date\s*:?\s*([A-Za-z]+\s+\d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_date = match.group(1)
            norm_date = normalize_date_string(raw_date)
            if norm_date:
                return norm_date, ConfidenceLevel.HIGH, match.group(0)

        # Fallback date pattern
        fallback = r"\b([A-Za-z]+\s+\d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2})\b"
        matches = list(re.finditer(fallback, text, re.IGNORECASE))
        if len(matches) >= 1:
            raw_date = matches[0].group(1)
            norm_date = normalize_date_string(raw_date)
            if norm_date:
                return norm_date, ConfidenceLevel.MEDIUM, matches[0].group(0)

        return None, ConfidenceLevel.NOT_FOUND, None

    @staticmethod
    def _extract_maturity_date(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        pattern = r"(?:maturity|expiry|end|termination)\s+date\s*:?\s*([A-Za-z]+\s+\d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_date = match.group(1)
            norm_date = normalize_date_string(raw_date)
            if norm_date:
                return norm_date, ConfidenceLevel.HIGH, match.group(0)

        # Fallback second date match if 2 dates present in text
        fallback = r"\b([A-Za-z]+\s+\d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2})\b"
        matches = list(re.finditer(fallback, text, re.IGNORECASE))
        if len(matches) >= 2:
            raw_date = matches[1].group(1)
            norm_date = normalize_date_string(raw_date)
            if norm_date:
                return norm_date, ConfidenceLevel.MEDIUM, matches[1].group(0)

        return None, ConfidenceLevel.NOT_FOUND, None

    @staticmethod
    def _extract_payment_frequency(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        # Semi-annual / bi-annual
        if re.search(r"\b(?:semi[- ]?annual|bi[- ]?annual|half[- ]?year(?:ly)?|semiannual)\b", text, re.IGNORECASE):
            return "SEMI_ANNUAL", ConfidenceLevel.HIGH, "SEMI_ANNUAL"

        if re.search(r"\b(?:monthly|per\s+month|each\s+month)\b", text, re.IGNORECASE):
            return "MONTHLY", ConfidenceLevel.HIGH, "MONTHLY"

        if re.search(r"\b(?:quarterly|per\s+quarter|every\s+3\s+months?)\b", text, re.IGNORECASE):
            return "QUARTERLY", ConfidenceLevel.HIGH, "QUARTERLY"

        if re.search(r"\b(?:annual(?:ly)?|per\s+year|yearly|once\s+a\s+year)\b", text, re.IGNORECASE):
            return "ANNUAL", ConfidenceLevel.MEDIUM, "ANNUAL"

        return None, ConfidenceLevel.NOT_FOUND, None
