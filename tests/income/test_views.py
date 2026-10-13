from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.income.models import Income


class IncomeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.other = User.objects.create(firebase_uid="uid-2", email="o@example.com", name="o")
        self.client.force_authenticate(user=self.user)

    def _valid_payload(self, **overrides):
        data = {"source": "salary", "amount": "50000.00", "income_date": str(date.today())}
        data.update(overrides)
        return data

    def test_create_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post("/api/income/", self._valid_payload())
        self.assertEqual(response.status_code, 401)

    def test_create_income_success(self):
        response = self.client.post("/api/income/", self._valid_payload())
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Income.objects.get(id=response.data["id"]).user, self.user)

    def test_create_income_rejects_invalid_source(self):
        response = self.client.post("/api/income/", self._valid_payload(source="crypto"))
        self.assertEqual(response.status_code, 400)

    def test_create_income_rejects_zero_amount(self):
        response = self.client.post("/api/income/", self._valid_payload(amount="0"))
        self.assertEqual(response.status_code, 400)

    def test_list_only_shows_own_income(self):
        Income.objects.create(source="salary", amount="1000", income_date=date.today(), user=self.user)
        Income.objects.create(source="bonus", amount="2000", income_date=date.today(), user=self.other)
        response = self.client.get("/api/income/")
        self.assertEqual(len(response.data), 1)

    def _create_income_for(self, user):
        return Income.objects.create(source="salary", amount="1000", income_date=date.today(), user=user)

    def test_get_own_income_succeeds(self):
        income = self._create_income_for(self.user)
        response = self.client.get(f"/api/income/{income.id}/")
        self.assertEqual(response.status_code, 200)

    def test_get_another_users_income_returns_404(self):
        income = self._create_income_for(self.other)
        response = self.client.get(f"/api/income/{income.id}/")
        self.assertEqual(response.status_code, 404)

    def test_update_own_income_succeeds(self):
        income = self._create_income_for(self.user)
        response = self.client.put(f"/api/income/{income.id}/", self._valid_payload(amount="2000"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["amount"], "2000.00")

    def test_delete_own_income_succeeds(self):
        income = self._create_income_for(self.user)
        response = self.client.delete(f"/api/income/{income.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Income.objects.filter(id=income.id).exists())

    def test_delete_another_users_income_returns_404(self):
        income = self._create_income_for(self.other)
        response = self.client.delete(f"/api/income/{income.id}/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Income.objects.filter(id=income.id).exists())
