from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.categories.models import Category
from apps.expenses.repositories import ExpenseRepository
from apps.expenses.services import ExpenseService
from common.exceptions import ValidationError


class ExpenseServiceTests(TestCase):
    def setUp(self):
        self.service = ExpenseService(repository=ExpenseRepository())
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.other_user = User.objects.create(firebase_uid="uid-2", email="o@example.com", name="o")
        self.default_category = Category.objects.get(name="Food", created_by=None)
        self.own_category = Category.objects.create(
            created_by=self.user, name="Gym", icon="x", color="#111111"
        )
        self.other_category = Category.objects.create(
            created_by=self.other_user, name="Private", icon="x", color="#222222"
        )

    def _create(self, **overrides):
        data = dict(
            user=self.user, category=self.default_category, title="Coffee",
            amount=Decimal("5.00"), payment_method="cash", expense_date=date.today(),
        )
        data.update(overrides)
        return self.service.create_expense(**data)

    def test_create_expense_with_default_category_succeeds(self):
        expense = self._create()
        self.assertEqual(expense.category, self.default_category)

    def test_create_expense_with_own_category_succeeds(self):
        expense = self._create(category=self.own_category)
        self.assertEqual(expense.category, self.own_category)

    def test_create_expense_with_another_users_category_rejected(self):
        with self.assertRaises(ValidationError):
            self._create(category=self.other_category)

    def test_create_expense_rejects_zero_amount(self):
        with self.assertRaises(ValidationError):
            self._create(amount=Decimal("0"))

    def test_create_expense_rejects_negative_amount(self):
        with self.assertRaises(ValidationError):
            self._create(amount=Decimal("-1"))

    def test_create_expense_rejects_future_date(self):
        with self.assertRaises(ValidationError):
            self._create(expense_date=date.today() + timedelta(days=1))

    def test_create_expense_owned_by_given_user_not_client_supplied(self):
        expense = self._create()
        self.assertEqual(expense.user, self.user)

    def test_update_expense_rejects_moving_to_another_users_category(self):
        expense = self._create()
        with self.assertRaises(ValidationError):
            self.service.update_expense(self.user, expense, category=self.other_category)

    def test_update_expense_rejects_negative_amount(self):
        expense = self._create()
        with self.assertRaises(ValidationError):
            self.service.update_expense(self.user, expense, amount=Decimal("-10"))

    def test_update_expense_valid_change_succeeds(self):
        expense = self._create()
        updated = self.service.update_expense(self.user, expense, title="Updated Coffee")
        self.assertEqual(updated.title, "Updated Coffee")
