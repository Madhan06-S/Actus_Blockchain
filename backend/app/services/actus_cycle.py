"""Utility for generating deterministic ACTUS cycle schedule dates adhering to strict calendar rules."""

import calendar
from datetime import datetime, timezone
from typing import List


def add_calendar_months(dt: datetime, months: int) -> datetime:
    """Add N calendar months to a datetime, clamping the day to max days in the target month.
    
    Example: Jan 31 + 1 month -> Feb 28 (or Feb 29 in leap year).
    Ensures calendar-accurate arithmetic without 30-day approximations.
    """
    total_months = dt.month - 1 + months
    target_year = dt.year + total_months // 12
    target_month = total_months % 12 + 1
    max_days = calendar.monthrange(target_year, target_month)[1]
    target_day = min(dt.day, max_days)
    return dt.replace(year=target_year, month=target_month, day=target_day)


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO 8601 string into a timezone-aware UTC datetime."""
    clean_str = dt_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(clean_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def format_iso_datetime(dt: datetime) -> str:
    """Format a datetime into a clean ISO 8601 UTC string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def generate_cycle_dates(
    start_date: datetime,
    end_date: datetime,
    cycle: str,
    anchor_date: datetime,
) -> List[datetime]:
    """Generate recurring schedule dates given start, end, cycle duration, and anchor date.
    
    Supports 'P1M' (monthly), 'P3M' (quarterly), 'P6M' (semi-annual), 'P1Y' (annual).
    Does NOT generate dates strictly after end_date.
    """
    cycle_months_map = {
        "P1M": 1,
        "P3M": 3,
        "P6M": 6,
        "P1Y": 12,
    }

    if cycle not in cycle_months_map:
        raise ValueError(f"Unsupported cycle duration format '{cycle}'. Supported cycles: P1M, P3M, P6M, P1Y.")

    months_increment = cycle_months_map[cycle]
    dates: List[datetime] = []

    current_date = anchor_date
    step = 0

    while current_date <= end_date:
        if current_date >= start_date:
            dates.append(current_date)

        step += 1
        current_date = add_calendar_months(anchor_date, step * months_increment)

    return dates
