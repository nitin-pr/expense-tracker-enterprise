import calendar
from datetime import date
from typing import Tuple


def month_bounds(year: int, month: int) -> Tuple[date, date]:
    """First and last calendar day of a given month/year, inclusive."""
    _, last_day = calendar.monthrange(year, month)
    return date(year, month, 1), date(year, month, last_day)
