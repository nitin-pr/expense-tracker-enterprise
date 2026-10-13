from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.budgets.observers import BudgetObserver

from .models import Notification


class NotificationService(BudgetObserver):
    """
    Minimal implementation for Sprint 4: persists a Notification row directly,
    rather than the full NotificationChannel/NotificationDispatcher Strategy
    abstraction from the LLD (multiple delivery channels, dispatch fan-out).
    That richness is US-027's job (Sprint 5), once a second real channel
    actually exists to justify it - a one-implementation "Strategy" isn't
    pulling its weight yet. This class only needs to exist at all because
    US-025/026 need *some* real, persisted, race-safe side effect to prove
    the threshold-crossing mechanism actually works.
    """

    def on_threshold_crossed(self, user, budget, spent, percent, threshold_tier):
        # Same formatting-consistency fix as BudgetService.get_status: a raw
        # Decimal from a Sum() aggregate can render with a different number
        # of trailing digits than one read straight from the DB.
        cents = Decimal("0.01")
        title = f"Budget {threshold_tier}% threshold reached"
        message = (
            f"You've spent {spent.quantize(cents)} of your {budget.budget.quantize(cents)} "
            f"budget ({percent}%) this month."
        )
        try:
            # Nested atomic() -> a SAVEPOINT when already inside an outer
            # transaction (BudgetService.evaluate_threshold_for_period's own
            # atomic block, or a test's). Without this, catching IntegrityError
            # in plain Python doesn't recover the connection - Django leaves the
            # whole enclosing transaction "broken" until a savepoint rolls back
            # just this one failed statement. Confirmed this the hard way: every
            # query after the uncaught case raised TransactionManagementError.
            with transaction.atomic():
                Notification.objects.create(
                    user=user,
                    budget=budget,
                    threshold_tier=threshold_tier,
                    title=title,
                    message=message,
                    kind="budget_exceeded",
                )
        except IntegrityError:
            # UNIQUE(budget, threshold_tier) backstop caught a duplicate -
            # already notified for this tier, nothing more to do.
            pass
