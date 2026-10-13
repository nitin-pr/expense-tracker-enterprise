from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.categories.models import Category
from apps.expenses.models import Expense


class BudgetViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.category = Category.objects.get(name="Food", created_by=None)
        self.client.force_authenticate(user=self.user)

    def test_create_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post("/api/budgets/", {"month": 1, "year": 2026, "budget": "1000.00"})
        self.assertEqual(response.status_code, 401)

    def test_create_budget_success(self):
        response = self.client.post("/api/budgets/", {"month": 1, "year": 2026, "budget": "1000.00"})
        self.assertEqual(response.status_code, 201)

    def test_create_duplicate_budget_rejected(self):
        self.client.post("/api/budgets/", {"month": 1, "year": 2026, "budget": "1000.00"})
        response = self.client.post("/api/budgets/", {"month": 1, "year": 2026, "budget": "2000.00"})
        self.assertEqual(response.status_code, 400)

    def test_create_budget_rejects_zero_amount(self):
        response = self.client.post("/api/budgets/", {"month": 1, "year": 2026, "budget": "0"})
        self.assertEqual(response.status_code, 400)

    def test_get_status_for_period_with_no_budget_returns_404(self):
        response = self.client.get("/api/budgets/?month=1&year=2026")
        self.assertEqual(response.status_code, 404)

    def test_get_status_returns_computed_values(self):
        self.client.post("/api/budgets/", {"month": 1, "year": 2026, "budget": "1000.00"})
        Expense.objects.create(
            title="x", amount="300.00", category=self.category, payment_method="cash",
            expense_date=date(2026, 1, 10), user=self.user,
        )
        response = self.client.get("/api/budgets/?month=1&year=2026")
        self.assertEqual(response.status_code, 200)
        # response.data is the pre-render Python dict (raw Decimal objects,
        # not yet JSON-stringified) - compare against Decimal, not str.
        self.assertEqual(response.data["spent"], Decimal("300.00"))
        self.assertEqual(response.data["remaining"], Decimal("700.00"))
        self.assertEqual(response.data["percent_used"], 30)

    def test_get_status_rejects_non_numeric_month(self):
        response = self.client.get("/api/budgets/?month=abc&year=2026")
        self.assertEqual(response.status_code, 400)
