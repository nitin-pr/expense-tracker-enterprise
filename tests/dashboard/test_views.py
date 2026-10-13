from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User


class DashboardSummaryViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.client.force_authenticate(user=self.user)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 401)

    def test_returns_all_five_summary_fields_for_brand_new_user(self):
        response = self.client.get("/api/dashboard/")

        self.assertEqual(response.status_code, 200)
        for field in ["today_expense", "monthly_expense", "monthly_income", "remaining_budget", "total_categories"]:
            self.assertIn(field, response.data)
        self.assertEqual(response.data["total_categories"], 10)
        self.assertIsNone(response.data["remaining_budget"])
