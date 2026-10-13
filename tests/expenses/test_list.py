from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.categories.models import Category
from apps.expenses.models import Expense


class ExpenseListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.other = User.objects.create(firebase_uid="uid-2", email="o@example.com", name="o")
        self.food = Category.objects.get(name="Food", created_by=None)
        self.travel = Category.objects.get(name="Travel", created_by=None)
        self.client.force_authenticate(user=self.user)

        self._make("Coffee", "4.50", self.food, "cash", date(2026, 1, 5), description="morning brew")
        self._make("Flight tickets", "300.00", self.travel, "card", date(2026, 1, 10))
        self._make("Groceries", "60.00", self.food, "upi", date(2026, 1, 15))
        self._make("Other user's expense", "10.00", self.food, "cash", date(2026, 1, 1), user=self.other)

    def _make(self, title, amount, category, payment_method, expense_date, description="", user=None):
        return Expense.objects.create(
            title=title, amount=amount, category=category, payment_method=payment_method,
            expense_date=expense_date, description=description, user=user or self.user,
        )

    def test_list_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/expenses/")
        self.assertEqual(response.status_code, 401)

    def test_list_scoped_to_requesting_user_only(self):
        response = self.client.get("/api/expenses/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)  # not 4 - other user's expense excluded

    def test_list_has_pagination_envelope(self):
        response = self.client.get("/api/expenses/")
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

    def test_list_default_ordering_is_newest_first(self):
        response = self.client.get("/api/expenses/")
        titles = [item["title"] for item in response.data["results"]]
        self.assertEqual(titles, ["Groceries", "Flight tickets", "Coffee"])

    def test_search_matches_title_case_insensitively(self):
        response = self.client.get("/api/expenses/?search=COFFEE")
        titles = [item["title"] for item in response.data["results"]]
        self.assertEqual(titles, ["Coffee"])

    def test_search_matches_description(self):
        response = self.client.get("/api/expenses/?search=brew")
        titles = [item["title"] for item in response.data["results"]]
        self.assertEqual(titles, ["Coffee"])

    def test_empty_search_returns_full_list(self):
        response = self.client.get("/api/expenses/?search=")
        self.assertEqual(response.data["count"], 3)

    def test_filter_by_category(self):
        response = self.client.get(f"/api/expenses/?category={self.travel.id}")
        titles = [item["title"] for item in response.data["results"]]
        self.assertEqual(titles, ["Flight tickets"])

    def test_filter_by_date_range(self):
        response = self.client.get("/api/expenses/?date_from=2026-01-06&date_to=2026-01-31")
        titles = {item["title"] for item in response.data["results"]}
        self.assertEqual(titles, {"Flight tickets", "Groceries"})

    def test_filter_by_invalid_date_range_rejected(self):
        response = self.client.get("/api/expenses/?date_from=2026-01-31&date_to=2026-01-01")
        self.assertEqual(response.status_code, 400)

    def test_filter_by_amount_range(self):
        response = self.client.get("/api/expenses/?amount_min=5&amount_max=100")
        titles = [item["title"] for item in response.data["results"]]
        self.assertEqual(titles, ["Groceries"])

    def test_filter_by_payment_method(self):
        response = self.client.get("/api/expenses/?payment_method=upi")
        titles = [item["title"] for item in response.data["results"]]
        self.assertEqual(titles, ["Groceries"])

    def test_sort_by_amount_ascending(self):
        response = self.client.get("/api/expenses/?ordering=amount")
        titles = [item["title"] for item in response.data["results"]]
        self.assertEqual(titles, ["Coffee", "Groceries", "Flight tickets"])

    def test_sort_rejects_disallowed_field(self):
        response = self.client.get("/api/expenses/?ordering=user__email")
        self.assertEqual(response.status_code, 400)

    def test_pagination_page_size(self):
        response = self.client.get("/api/expenses/?page_size=2")
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNotNone(response.data["next"])

    def test_pagination_invalid_numeric_param_rejected(self):
        response = self.client.get("/api/expenses/?amount_min=not-a-number")
        self.assertEqual(response.status_code, 400)
