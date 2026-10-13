from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from common.exceptions import ValidationError

ALLOWED_ORDERING = {"expense_date", "-expense_date", "amount", "-amount"}
DEFAULT_ORDERING = "-expense_date"


@dataclass
class ExpenseFilter:
    """Value object carrying search/filter/sort params through View -> Service -> Repository,
    so the repository builds one queryset, not N. Per LLD S4."""

    search: Optional[str] = None
    category_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    payment_method: Optional[str] = None
    ordering: str = DEFAULT_ORDERING

    @classmethod
    def from_query_params(cls, params) -> "ExpenseFilter":
        filters = cls(
            search=params.get("search") or None,
            category_id=_parse_int(params, "category"),
            date_from=_parse_date(params, "date_from"),
            date_to=_parse_date(params, "date_to"),
            amount_min=_parse_decimal(params, "amount_min"),
            amount_max=_parse_decimal(params, "amount_max"),
            payment_method=params.get("payment_method") or None,
            ordering=params.get("ordering") or DEFAULT_ORDERING,
        )

        if filters.date_from and filters.date_to and filters.date_from > filters.date_to:
            raise ValidationError("'date_from' must not be after 'date_to'.")
        if filters.ordering not in ALLOWED_ORDERING:
            raise ValidationError(
                f"Invalid ordering '{filters.ordering}'. Allowed: {', '.join(sorted(ALLOWED_ORDERING))}."
            )
        return filters


def _parse_date(params, key):
    value = params.get(key)
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError(f"'{key}' must be a valid date (YYYY-MM-DD), got '{value}'.")


def _parse_decimal(params, key):
    value = params.get(key)
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        raise ValidationError(f"'{key}' must be a valid number, got '{value}'.")


def _parse_int(params, key):
    value = params.get(key)
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f"'{key}' must be a valid integer, got '{value}'.")
