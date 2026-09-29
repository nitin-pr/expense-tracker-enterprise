from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import User
from apps.categories.models import Category
from apps.expenses.models import Expense


class ExpenseModelConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.category = Category.objects.get(name="Food", created_by=None)

    def _make(self, **overrides):
        data = dict(
            title="Coffee", amount=Decimal("5.00"), category=self.category,
            payment_method="cash", expense_date=date(2026, 1, 1), user=self.user,
        )
        data.update(overrides)
        return Expense.objects.create(**data)

    def test_amount_must_be_positive(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._make(amount=Decimal("0"))

    def test_negative_amount_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._make(amount=Decimal("-5.00"))

    def test_valid_expense_creates_successfully(self):
        expense = self._make()
        self.assertEqual(expense.title, "Coffee")

    def test_category_restrict_blocks_deletion_while_referenced(self):
        self._make()
        with self.assertRaises(Exception):  # RestrictedError, verified precisely in categories service tests
            with transaction.atomic():
                self.category.delete()
        # The category must still exist - the delete was blocked, not silently no-op'd.
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())
