from datetime import date
from common.exceptions import ValidationError

def validate_not_future_date(value: date) -> None:
    if value > date.today():
        raise ValidationError(f"Date cannot be in the future, got {value}.")