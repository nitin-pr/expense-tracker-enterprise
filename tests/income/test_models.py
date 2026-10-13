from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import User
from apps.income.models import Income


class IncomeModelConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")

    def test_amount_must_be_positive(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Income.objects.create(
                    source="salary", amount=Decimal("0"), income_date=date.today(), user=self.user
                )

    def test_valid_income_creates_successfully(self):
        income = Income.objects.create(
            source="salary", amount=Decimal("50000"), income_date=date.today(), user=self.user
        )
        self.assertEqual(income.source, "salary")
