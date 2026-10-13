from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import User
from apps.budgets.models import Budget


class BudgetModelConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")

    def test_valid_budget_creates_successfully(self):
        budget = Budget.objects.create(user=self.user, month=1, year=2026, budget=Decimal("50000"))
        self.assertEqual(budget.month, 1)

    def test_duplicate_period_for_same_user_rejected(self):
        Budget.objects.create(user=self.user, month=1, year=2026, budget=Decimal("50000"))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Budget.objects.create(user=self.user, month=1, year=2026, budget=Decimal("60000"))

    def test_same_period_different_users_allowed(self):
        other = User.objects.create(firebase_uid="uid-2", email="o@example.com", name="o")
        Budget.objects.create(user=self.user, month=1, year=2026, budget=Decimal("50000"))
        Budget.objects.create(user=other, month=1, year=2026, budget=Decimal("30000"))
        self.assertEqual(Budget.objects.filter(month=1, year=2026).count(), 2)

    def test_zero_budget_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Budget.objects.create(user=self.user, month=1, year=2026, budget=Decimal("0"))

    def test_invalid_month_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Budget.objects.create(user=self.user, month=13, year=2026, budget=Decimal("100"))
