from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.categories.models import Category
from apps.expenses.repositories import ExpenseRepository
from apps.expenses.services import ExpenseService
from apps.notifications.models import Notification


class NotificationListViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.other = User.objects.create(firebase_uid="uid-2", email="o@example.com", name="o")
        self.client.force_authenticate(user=self.user)

    def test_list_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, 401)

    def test_list_empty_when_no_notifications(self):
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_list_only_shows_own_notifications(self):
        Notification.objects.create(user=self.user, title="mine", message="m", kind="daily_reminder")
        Notification.objects.create(user=self.other, title="theirs", message="m", kind="daily_reminder")

        response = self.client.get("/api/notifications/")

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "mine")

    def test_threshold_crossing_is_visible_through_the_list_endpoint(self):
        # End-to-end proof of US-027's actual AC, not just the model/channel
        # pieces in isolation: create a budget, cross a threshold via a real
        # expense, then confirm it's retrievable via GET /api/notifications/.
        from apps.budgets.repositories import BudgetRepository
        from apps.budgets.services import BudgetService

        category = Category.objects.get(name="Food", created_by=None)
        BudgetService(repository=BudgetRepository()).create_budget(self.user, 1, 2026, Decimal("1000"))
        ExpenseService(repository=ExpenseRepository()).create_expense(
            user=self.user, category=category, title="x", amount=Decimal("850"),
            payment_method="cash", expense_date=date(2026, 1, 15),
        )

        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["kind"], "budget_exceeded")
        self.assertEqual(response.data[0]["threshold_tier"], 80)
