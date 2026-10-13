from enum import IntEnum


class BudgetThreshold(IntEnum):
    """
    Plain IntEnum, not Django's IntegerChoices - this isn't a model field's
    choice set (only Notification.threshold_tier stores one of these values,
    and that field's own CHECK constraint lists the raw integers directly).
    This enum exists purely for comparison logic inside BudgetService.
    """

    WARNING = 80
    HIGH = 90
    EXCEEDED = 100
