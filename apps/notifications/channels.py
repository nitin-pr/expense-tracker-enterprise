import logging
from abc import ABC, abstractmethod
from decimal import Decimal

from django.db import IntegrityError, transaction

from .models import Notification

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Real ABC, same reasoning as AuthProvider/BudgetObserver - no sensible
    default exists for "deliver this notification"; every channel has to
    actually implement its own delivery mechanism."""

    @abstractmethod
    def send(self, user, title, message, kind, budget=None, threshold_tier=None):
        ...


class InAppNotificationChannel(NotificationChannel):
    """
    "Delivery" for this channel specifically IS persisting the Notification
    row - the in-app inbox (GET /api/notifications/) is just a query against
    this table, so there's no separate delivery step beyond writing the row.
    """

    def send(self, user, title, message, kind, budget=None, threshold_tier=None):
        try:
            # Nested atomic() -> a SAVEPOINT when already inside an outer
            # transaction. Without this, catching IntegrityError in plain
            # Python doesn't recover the connection - confirmed this the hard
            # way in Sprint 4 (every later query raised TransactionManagementError).
            with transaction.atomic():
                Notification.objects.create(
                    user=user, budget=budget, threshold_tier=threshold_tier,
                    title=title, message=message, kind=kind,
                )
        except IntegrityError:
            # UNIQUE(budget, threshold_tier) backstop caught a duplicate -
            # already notified for this tier, nothing more to do.
            pass


class NotificationDispatcher:
    """
    Tries every configured channel independently - per US-027's AC, "a
    threshold-crossing event always produces a visible in-app notification
    even if other channels fail." With only one channel today this clause
    is forward-looking (no second channel exists yet to actually fail), but
    the dispatcher is built so that guarantee holds the moment one does
    (US-028, email) without needing to revisit this code.
    """

    def __init__(self, channels):
        self.channels = channels

    def dispatch(self, user, title, message, kind, budget=None, threshold_tier=None):
        for channel in self.channels:
            try:
                channel.send(user, title, message, kind, budget=budget, threshold_tier=threshold_tier)
            except Exception:
                logger.exception("Notification channel %s failed to deliver", type(channel).__name__)


def compose_budget_threshold_message(budget, spent, percent, threshold_tier):
    cents = Decimal("0.01")
    title = f"Budget {threshold_tier}% threshold reached"
    message = (
        f"You've spent {spent.quantize(cents)} of your {budget.budget.quantize(cents)} "
        f"budget ({percent}%) this month."
    )
    return title, message
