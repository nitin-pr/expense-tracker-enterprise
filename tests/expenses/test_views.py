from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.categories.models import Category
from apps.expenses.models import Expense


class ExpenseViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.other = User.objects.create(firebase_uid="uid-2", email="o@example.com", name="o")
        self.category = Category.objects.get(name="Food", created_by=None)
        self.client.force_authenticate(user=self.user)

    def _valid_payload(self, **overrides):
        data = {
            "title": "Coffee",
            "amount": "5.00",
            "category": self.category.id,
            "payment_method": "cash",
            "expense_date": str(date.today()),
        }
        data.update(overrides)
        return data

    def test_create_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post("/api/expenses/", self._valid_payload())
        self.assertEqual(response.status_code, 401)

    def test_create_expense_success(self):
        response = self.client.post("/api/expenses/", self._valid_payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Coffee")
        self.assertEqual(Expense.objects.get(id=response.data["id"]).user, self.user)

    def test_create_expense_rejects_zero_amount(self):
        response = self.client.post("/api/expenses/", self._valid_payload(amount="0"))
        self.assertEqual(response.status_code, 400)

    def test_create_expense_rejects_future_date(self):
        future = str(date.today() + timedelta(days=5))
        response = self.client.post("/api/expenses/", self._valid_payload(expense_date=future))
        self.assertEqual(response.status_code, 400)

    def test_create_expense_rejects_invalid_payment_method(self):
        response = self.client.post("/api/expenses/", self._valid_payload(payment_method="bitcoin"))
        self.assertEqual(response.status_code, 400)

    def test_create_expense_rejects_another_users_category(self):
        other_cat = Category.objects.create(created_by=self.other, name="Private", icon="x", color="#111111")
        response = self.client.post("/api/expenses/", self._valid_payload(category=other_cat.id))
        self.assertEqual(response.status_code, 400)

    def _create_expense_for(self, user):
        return Expense.objects.create(
            title="Lunch", amount="10.00", category=self.category,
            payment_method="card", expense_date=date.today(), user=user,
        )

    def test_get_own_expense_succeeds(self):
        expense = self._create_expense_for(self.user)
        response = self.client.get(f"/api/expenses/{expense.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Lunch")

    def test_get_another_users_expense_returns_404_not_403(self):
        expense = self._create_expense_for(self.other)
        response = self.client.get(f"/api/expenses/{expense.id}/")
        self.assertEqual(response.status_code, 404)

    def test_get_nonexistent_expense_returns_404(self):
        response = self.client.get("/api/expenses/999999/")
        self.assertEqual(response.status_code, 404)

    def test_update_own_expense_succeeds(self):
        expense = self._create_expense_for(self.user)
        response = self.client.put(f"/api/expenses/{expense.id}/", self._valid_payload(title="Dinner"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Dinner")

    def test_update_another_users_expense_returns_404(self):
        expense = self._create_expense_for(self.other)
        response = self.client.put(f"/api/expenses/{expense.id}/", self._valid_payload(title="Hacked"))
        self.assertEqual(response.status_code, 404)

    def test_delete_own_expense_succeeds(self):
        expense = self._create_expense_for(self.user)
        response = self.client.delete(f"/api/expenses/{expense.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Expense.objects.filter(id=expense.id).exists())

    def test_delete_another_users_expense_returns_404(self):
        expense = self._create_expense_for(self.other)
        response = self.client.delete(f"/api/expenses/{expense.id}/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Expense.objects.filter(id=expense.id).exists())
