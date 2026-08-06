from decimal import Decimal
from common.exceptions import ValidationError

def validate_positive_amount(value: Decimal) -> None:
    if value <= 0:
        raise ValidationError(f"Amount must be greater than zero, got {value}.")