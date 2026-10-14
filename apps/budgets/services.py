from decimal import Decimal

from django.db import transaction

from common.constants import BudgetThreshold
from common.exceptions import NotFoundError, ValidationError
from common.services import BaseService
from common.utils import month_bounds
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
        return self._build_status(budget, spent)

    def _build_status(self, budget, spent):
        percent_used = int((spent / budget.budget) * 100) if budget.budget else 0
        cents = Decimal("0.01")
        return {
            "id": budget.id,
            "month": budget.month,
            "year": budget.year,
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

    def get_budget_for_user(self, user, budget_id):
        # Same 404-not-403 fold as Expense/Income: a budget is never visible
        # cross-user, so "not found" and "not yours" return the same response.
        budget = self.repository.get_by_id(budget_id)
        if budget is None or budget.user_id != user.id:
            raise NotFoundError(f"Budget {budget_id} not found.")
        return budget

    def get_status_for_budget(self, budget):
        spent = self._compute_spent(budget.user, budget.month, budget.year)
        return self._build_status(budget, spent)

    def update_budget(self, budget, budget_amount):
        # Amount only - month/year are immutable once a budget exists (they're
        # part of the UniqueConstraint identity, not an editable attribute).
        validate_positive_amount(budget_amount)
        return self.repository.update(budget, budget=budget_amount)

    def delete_budget(self, budget):
        # Notification.budget has on_delete=CASCADE, so this also clears every
        # threshold notification tied to this budget - the only way to reset
        # the UNIQUE(budget, threshold_tier) backstop once a tier has fired.
        self.repository.delete(budget)

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

        date_from, date_to = month_bounds(year, month)
        return ExpenseRepository().sum_for_period(user, date_from, date_to)


class BudgetThresholdEvaluator:
    """
    Thin wrapper so ExpenseService depends on a narrow evaluation interface,
    not all of BudgetService (budget creation, status queries, etc.) - per LLD S6.
    """

    def evaluate(self, user, expense_date):
        BudgetService(repository=BudgetRepository()).evaluate_threshold_for_period(
            user, expense_date.month, expense_date.year
        )
