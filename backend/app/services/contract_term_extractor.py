"""Service for extracting candidate financial contract terms from raw text using rule-based pattern matching."""

from datetime import datetime
import re
from typing import Dict, List, Optional, Tuple

from app.models.document import ConfidenceLevel
from app.schemas.document import ExtractedTermsResponse, FieldExtractionResult


def normalize_date_string(date_str: str) -> Optional[str]:
    """Parse date strings like 'January 1, 2027' or '2027-01-01' into 'YYYY-MM-DD'."""
    cleaned = date_str.strip()
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

        # 1. Currency Extraction
        curr_val, curr_conf, curr_src = cls._extract_currency(text)
        if curr_val:
            fields["currency"] = FieldExtractionResult(value=curr_val, confidence=curr_conf, source=curr_src)
        else:
            fields["currency"] = FieldExtractionResult(value=None, confidence=ConfidenceLevel.NOT_FOUND, source=None)
            missing_fields.append("currency")

        # 2. Principal Extraction
        p_val, p_conf, p_src = cls._extract_principal(text)
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

    @staticmethod
    def _extract_currency(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        if "₹" in text or "\u25a0" in text or re.search(r"\b(?:INR|Rs\.?)\b", text, re.IGNORECASE):
            return "INR", ConfidenceLevel.HIGH, "INR"
        if "$" in text or re.search(r"\bUSD\b", text, re.IGNORECASE):
            return "USD", ConfidenceLevel.HIGH, "USD"
        if "€" in text or re.search(r"\bEUR\b", text, re.IGNORECASE):
            return "EUR", ConfidenceLevel.HIGH, "EUR"
        if "£" in text or re.search(r"\bGBP\b", text, re.IGNORECASE):
            return "GBP", ConfidenceLevel.HIGH, "GBP"
        return None, ConfidenceLevel.NOT_FOUND, None

    @staticmethod
    def _extract_principal(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        # Pattern 1: "Principal amount: ₹100,000", "loan amount of INR 100,000", or "loan amount of 100,000"
        pattern1 = r"(?:principal(?:\s+amount)?|loan\s+amount(?:\s+of)?|sum\s+of)\s*:?\s*[^\d\s]*\s*([\d,]+(?:\.\d+)?)"
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            raw_val = match.group(1).replace(",", "")
            return raw_val, ConfidenceLevel.HIGH, match.group(0)

        # Pattern 2: "INR 100,000" or "₹100,000"
        pattern2 = r"(?:INR|USD|EUR|GBP|₹|\$|€|£)\s*([\d,]+(?:\.\d+)?)"
        match2 = re.search(pattern2, text, re.IGNORECASE)
        if match2:
            raw_val = match2.group(1).replace(",", "")
            return raw_val, ConfidenceLevel.MEDIUM, match2.group(0)

        # Pattern 3: "100000 INR"
        pattern3 = r"([\d,]+(?:\.\d+)?)\s*(?:INR|USD|EUR|GBP)"
        match3 = re.search(pattern3, text, re.IGNORECASE)
        if match3:
            raw_val = match3.group(1).replace(",", "")
            return raw_val, ConfidenceLevel.MEDIUM, match3.group(0)

        return None, ConfidenceLevel.NOT_FOUND, None

    @staticmethod
    def _extract_interest_rate(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        # Pattern 1: "annual interest rate: 10%" or "interest rate: 10% per annum"
        pattern1 = r"(?:annual\s+)?interest(?:\s+rate)?\s*:?\s*([\d.]+)\s*(?:%|percent)"
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return match.group(1), ConfidenceLevel.HIGH, match.group(0)

        # Pattern 2: "10% per annum", "10 percent annual interest", "10% annual interest"
        pattern2 = r"([\d.]+)\s*(?:%|percent)\s*(?:per\s+annum|annual|p\.a\.)?(?:\s+interest)?"
        match2 = re.search(pattern2, text, re.IGNORECASE)
        if match2:
            return match2.group(1), ConfidenceLevel.HIGH, match2.group(0)

        return None, ConfidenceLevel.NOT_FOUND, None

    @staticmethod
    def _extract_start_date(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        pattern = r"(?:start|commencement|inception|effective)\s+date\s*:?\s*([A-Za-z]+\s+\d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_date = match.group(1)
            norm_date = normalize_date_string(raw_date)
            if norm_date:
                return norm_date, ConfidenceLevel.HIGH, match.group(0)

        # Fallback date pattern
        fallback = r"\b([A-Za-z]+\s+\d{1,2},\s*\d{4})\b"
        matches = list(re.finditer(fallback, text, re.IGNORECASE))
        if len(matches) >= 1:
            raw_date = matches[0].group(1)
            norm_date = normalize_date_string(raw_date)
            if norm_date:
                return norm_date, ConfidenceLevel.MEDIUM, matches[0].group(0)

        return None, ConfidenceLevel.NOT_FOUND, None

    @staticmethod
    def _extract_maturity_date(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        pattern = r"(?:maturity|expiry|end)\s+date\s*:?\s*([A-Za-z]+\s+\d{1,2},\s*\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_date = match.group(1)
            norm_date = normalize_date_string(raw_date)
            if norm_date:
                return norm_date, ConfidenceLevel.HIGH, match.group(0)

        # Fallback second date match if 2 dates present in text
        fallback = r"\b([A-Za-z]+\s+\d{1,2},\s*\d{4})\b"
        matches = list(re.finditer(fallback, text, re.IGNORECASE))
        if len(matches) >= 2:
            raw_date = matches[1].group(1)
            norm_date = normalize_date_string(raw_date)
            if norm_date:
                return norm_date, ConfidenceLevel.MEDIUM, matches[1].group(0)

        return None, ConfidenceLevel.NOT_FOUND, None

    @staticmethod
    def _extract_payment_frequency(text: str) -> Tuple[Optional[str], ConfidenceLevel, Optional[str]]:
        if re.search(r"\bmonthly\b|payments?\s+shall\s+be\s+made\s+monthly|paid\s+monthly", text, re.IGNORECASE):
            return "MONTHLY", ConfidenceLevel.HIGH, "monthly"
        return None, ConfidenceLevel.NOT_FOUND, None
