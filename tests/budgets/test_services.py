from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.budgets.repositories import BudgetRepository
from apps.budgets.services import BudgetService
from apps.categories.models import Category
from apps.expenses.models import Expense
from apps.expenses.repositories import ExpenseRepository
from apps.expenses.services import ExpenseService
from apps.notifications.models import Notification
from common.exceptions import NotFoundError, ValidationError


class BudgetServiceTests(TestCase):
    def setUp(self):
        self.service = BudgetService(repository=BudgetRepository())
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.category = Category.objects.get(name="Food", created_by=None)

    def _add_expense_direct(self, amount, day=15):
        # Raw ORM create - bypasses ExpenseService, so does NOT trigger budget
        # evaluation. Used for tests that just need existing spend data.
        return Expense.objects.create(
            title="x", amount=amount, category=self.category, payment_method="cash",
            expense_date=date(2026, 1, day), user=self.user,
        )

    def _add_expense_via_service(self, amount, day=15):
        # Goes through the real ExpenseService, so DOES trigger budget
        # evaluation - used for tests proving the trigger itself works.
        return ExpenseService(repository=ExpenseRepository()).create_expense(
            user=self.user, category=self.category, title="x", amount=amount,
            payment_method="cash", expense_date=date(2026, 1, day),
        )

    def test_create_budget_success(self):
        budget = self.service.create_budget(self.user, 1, 2026, Decimal("1000"))
        self.assertEqual(budget.budget, Decimal("1000"))

    def test_create_budget_rejects_zero_amount(self):
        with self.assertRaises(ValidationError):
            self.service.create_budget(self.user, 1, 2026, Decimal("0"))

    def test_create_budget_rejects_duplicate_period(self):
        self.service.create_budget(self.user, 1, 2026, Decimal("1000"))
        with self.assertRaises(ValidationError):
            self.service.create_budget(self.user, 1, 2026, Decimal("2000"))

    def test_get_status_raises_not_found_when_no_budget(self):
        with self.assertRaises(NotFoundError):
            self.service.get_status(self.user, 1, 2026)

    def test_get_status_computes_spent_and_remaining(self):
        self.service.create_budget(self.user, 1, 2026, Decimal("1000"))
        self._add_expense_direct(Decimal("300"))
        status_data = self.service.get_status(self.user, 1, 2026)
        self.assertEqual(status_data["spent"], Decimal("300"))
        self.assertEqual(status_data["remaining"], Decimal("700"))
        self.assertEqual(status_data["percent_used"], 30)

    def test_get_status_remaining_can_go_negative(self):
        self.service.create_budget(self.user, 1, 2026, Decimal("100"))
        self._add_expense_direct(Decimal("150"))
        status_data = self.service.get_status(self.user, 1, 2026)
        self.assertEqual(status_data["remaining"], Decimal("-50"))

    def test_expense_creation_triggers_threshold_notification(self):
        # End-to-end through the real Observer chain registered in
        # apps/notifications/apps.py's ready() - not mocked.
        self.service.create_budget(self.user, 1, 2026, Decimal("1000"))
        self._add_expense_via_service(Decimal("850"))  # 85% -> crosses WARNING (80%)

        notification = Notification.objects.filter(user=self.user, threshold_tier=80).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.kind, "budget_exceeded")
        self.assertEqual(notification.budget.user, self.user)

    def test_crossing_directly_to_exceeded_fires_only_highest_tier(self):
        self.service.create_budget(self.user, 1, 2026, Decimal("1000"))
        self._add_expense_via_service(Decimal("1200"))  # 120% in one jump - skips 80/90 entirely

        self.assertEqual(Notification.objects.filter(user=self.user, threshold_tier=80).count(), 0)
        self.assertEqual(Notification.objects.filter(user=self.user, threshold_tier=90).count(), 0)
        self.assertEqual(Notification.objects.filter(user=self.user, threshold_tier=100).count(), 1)

    def test_below_warning_threshold_fires_no_notification(self):
        self.service.create_budget(self.user, 1, 2026, Decimal("1000"))
        self._add_expense_via_service(Decimal("200"))  # 20% - nowhere near 80%
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 0)

    def test_repeated_evaluation_at_same_tier_does_not_duplicate_notification(self):
        """
        Simulates what would happen if the SELECT FOR UPDATE lock somehow
        didn't prevent two evaluations reaching this point - notably, this
        IS the realistic scenario on SQLite specifically, since
        connection.features.has_select_for_update is False there (confirmed
        directly, not assumed) - select_for_update() silently no-ops on
        SQLite, unlike on Postgres where it does real row-level locking.
        So on this dev/test database, this test is exercising the *actual*
        defense in effect, not a hypothetical backup: NotificationService's
        IntegrityError catch against the UNIQUE(budget, threshold_tier)
        constraint is what is actually preventing the duplicate here.
        """
        self.service.create_budget(self.user, 1, 2026, Decimal("1000"))
        self._add_expense_via_service(Decimal("850"))
        self.assertEqual(Notification.objects.filter(user=self.user, threshold_tier=80).count(), 1)

        self.service.evaluate_threshold_for_period(self.user, 1, 2026)
        self.service.evaluate_threshold_for_period(self.user, 1, 2026)

        self.assertEqual(Notification.objects.filter(user=self.user, threshold_tier=80).count(), 1)

    def test_no_budget_set_does_not_raise_on_expense_creation(self):
        # create_expense always triggers evaluation regardless of whether a
        # budget exists yet - evaluate_threshold_for_period must no-op cleanly.
        self._add_expense_via_service(Decimal("50"))  # should not raise
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 0)
