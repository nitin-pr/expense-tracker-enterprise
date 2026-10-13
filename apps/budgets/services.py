import calendar
from datetime import date
from decimal import Decimal

from django.db import transaction

from common.constants import BudgetThreshold
from common.exceptions import NotFoundError, ValidationError
from common.services import BaseService
from common.validators import validate_positive_amount

from .models import Budget
from .repositories import BudgetRepository

# Highest tier first - a single expense pushing spend straight past 100% must
# fire only the EXCEEDED alert, not all three tiers in sequence.
_TIERS_HIGH_TO_LOW = (BudgetThreshold.EXCEEDED, BudgetThreshold.HIGH, BudgetThreshold.WARNING)


class BudgetService(BaseService):
    _observers = []

    @classmethod
    def register_observer(cls, observer):
        cls._observers.append(observer)

    def create_budget(self, user, month, year, budget_amount):
        validate_positive_amount(budget_amount)
        if self.repository.get_for_period(user, month, year) is not None:
            raise ValidationError(f"A budget already exists for {month}/{year}.")
        return self.repository.create(user=user, month=month, year=year, budget=budget_amount)

    def get_status(self, user, month, year):
        budget = self.repository.get_for_period(user, month, year)
        if budget is None:
            raise NotFoundError(f"No budget set for {month}/{year}.")
        spent = self._compute_spent(user, month, year)
        percent_used = int((spent / budget.budget) * 100) if budget.budget else 0
        cents = Decimal("0.01")
        return {
            # Explicitly quantized to 2 decimal places - a raw Decimal from
            # DB storage vs. one from a Sum() aggregate can render with a
            # different number of trailing digits (e.g. Decimal('300') vs
            # Decimal('300.00')), and this dict is returned directly in a
            # Response(), not through a DecimalField serializer that would
            # otherwise guarantee consistent formatting. Found via a test
            # that assumed "300.00" and got "300" instead.
            "budget": budget.budget.quantize(cents),
            "spent": spent.quantize(cents),
            "remaining": (budget.budget - spent).quantize(cents),  # deliberately allowed to go negative
            "percent_used": percent_used,
        }

    def evaluate_threshold_for_period(self, user, month, year):
        """
        Defense layer 1 (the common case): SELECT FOR UPDATE serializes
        concurrent evaluations for the same budget row, so a second concurrent
        call always sees the first call's already-committed expense before
        computing its own percentage - closing the race DATABASE_DESIGN.md
        describes. Defense layer 2 (the backstop) lives in NotificationService:
        even if this lock somehow didn't prevent a duplicate call from reaching
        here, the Notification table's UNIQUE(budget, threshold_tier) constraint
        makes a second insert for the same tier physically impossible.
        """
        with transaction.atomic():
            budget = Budget.objects.select_for_update().filter(
                user=user, month=month, year=year
            ).first()
            if budget is None or budget.budget <= 0:
                return

            spent = self._compute_spent(user, month, year)
            percent = int((spent / budget.budget) * 100)

            crossed_tier = next(
                (t.value for t in _TIERS_HIGH_TO_LOW if percent >= t.value), None
            )
            if crossed_tier is None:
                return

            for observer in self._observers:
                observer.on_threshold_crossed(user, budget, spent, percent, crossed_tier)

    def _compute_spent(self, user, month, year):
        from apps.expenses.repositories import ExpenseRepository

        _, last_day = calendar.monthrange(year, month)
        return ExpenseRepository().sum_for_period(user, date(year, month, 1), date(year, month, last_day))


class BudgetThresholdEvaluator:
    """
    Thin wrapper so ExpenseService depends on a narrow evaluation interface,
    not all of BudgetService (budget creation, status queries, etc.) - per LLD S6.
    """

    def evaluate(self, user, expense_date):
        BudgetService(repository=BudgetRepository()).evaluate_threshold_for_period(
            user, expense_date.month, expense_date.year
        )
