from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.income.repositories import IncomeRepository
from apps.income.services import IncomeService
from common.exceptions import ValidationError


class IncomeServiceTests(TestCase):
    def setUp(self):
        self.service = IncomeService(repository=IncomeRepository())
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")

    def test_create_income_success(self):
        income = self.service.create_income(self.user, "salary", Decimal("50000"), date.today())
        self.assertEqual(income.user, self.user)

    def test_create_income_rejects_zero_amount(self):
        with self.assertRaises(ValidationError):
            self.service.create_income(self.user, "salary", Decimal("0"), date.today())

    def test_create_income_rejects_negative_amount(self):
        with self.assertRaises(ValidationError):
            self.service.create_income(self.user, "salary", Decimal("-100"), date.today())

    def test_update_income_rejects_negative_amount(self):
        income = self.service.create_income(self.user, "salary", Decimal("1000"), date.today())
        with self.assertRaises(ValidationError):
            self.service.update_income(income, amount=Decimal("-1"))

    def test_sum_for_period(self):
        self.service.create_income(self.user, "salary", Decimal("1000"), date(2026, 1, 15))
        self.service.create_income(self.user, "bonus", Decimal("500"), date(2026, 1, 20))
        self.service.create_income(self.user, "salary", Decimal("1000"), date(2026, 2, 1))  # outside range

        total = self.service.repository.sum_for_period(self.user, date(2026, 1, 1), date(2026, 1, 31))
        self.assertEqual(total, Decimal("1500"))

    def test_get_monthly_total_sums_only_that_month(self):
        self.service.create_income(self.user, "salary", Decimal("1000"), date(2026, 1, 15))
        self.service.create_income(self.user, "bonus", Decimal("500"), date(2026, 2, 1))  # different month
        self.assertEqual(self.service.get_monthly_total(self.user, 1, 2026), Decimal("1000"))

    def test_get_monthly_total_zero_for_brand_new_user(self):
        self.assertEqual(self.service.get_monthly_total(self.user, 1, 2026), Decimal("0"))
