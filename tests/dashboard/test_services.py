from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.budgets.repositories import BudgetRepository
from apps.budgets.services import BudgetService
from apps.categories.models import Category
from apps.categories.repositories import CategoryRepository
from apps.categories.services import CategoryService
from apps.dashboard.services import DashboardService
from apps.expenses.models import Expense
from apps.income.models import Income


class DashboardServiceTests(TestCase):
    def setUp(self):
        self.service = DashboardService()
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.category = Category.objects.get(name="Food", created_by=None)

    def test_brand_new_user_gets_zero_values_not_errors_or_nulls_where_zero_is_expected(self):
        # The AC's explicit callout: no divide-by-zero, no nulls where zero
        # is expected. total_categories is correctly 10, not 0 - the 10
        # seeded defaults are genuinely available to every user, even one
        # who has never created anything themselves.
        summary = self.service.get_summary(self.user)

        self.assertEqual(summary["today_expense"], Decimal("0.00"))
        self.assertEqual(summary["monthly_expense"], Decimal("0.00"))
        self.assertEqual(summary["monthly_income"], Decimal("0.00"))
        self.assertEqual(summary["total_categories"], 10)
        # remaining_budget IS correctly null here - "no budget set" is a
        # genuinely different fact from "a $0 budget, fully spent."
        self.assertIsNone(summary["remaining_budget"])

    def test_aggregates_real_data_across_all_four_domains(self):
        today = date.today()
        Expense.objects.create(
            title="x", amount=Decimal("50"), category=self.category, payment_method="cash",
            expense_date=today, user=self.user,
        )
        Expense.objects.create(
            title="y", amount=Decimal("30"), category=self.category, payment_method="cash",
            expense_date=today.replace(day=1), user=self.user,
        )
        Income.objects.create(source="salary", amount=Decimal("1000"), income_date=today, user=self.user)
        BudgetService(repository=BudgetRepository()).create_budget(self.user, today.month, today.year, Decimal("500"))
        CategoryService(repository=CategoryRepository()).create_category(self.user, "Gym", "x", "#111111")

        summary = self.service.get_summary(self.user)

        self.assertEqual(summary["today_expense"], Decimal("50.00"))
        self.assertEqual(summary["monthly_expense"], Decimal("80.00"))  # 50 + 30, both this month
        self.assertEqual(summary["monthly_income"], Decimal("1000.00"))
        self.assertEqual(summary["remaining_budget"], Decimal("420.00"))  # 500 - 80
        self.assertEqual(summary["total_categories"], 11)  # 10 defaults + 1 custom

    def test_does_not_count_other_users_data(self):
        other = User.objects.create(firebase_uid="uid-2", email="o@example.com", name="o")
        Expense.objects.create(
            title="x", amount=Decimal("999"), category=self.category, payment_method="cash",
            expense_date=date.today(), user=other,
        )

        summary = self.service.get_summary(self.user)

        self.assertEqual(summary["today_expense"], Decimal("0.00"))

    def test_expenses_from_other_months_excluded_from_monthly_total(self):
        last_month = date.today().replace(day=1) - timedelta(days=1)
        Expense.objects.create(
            title="x", amount=Decimal("500"), category=self.category, payment_method="cash",
            expense_date=last_month, user=self.user,
        )

        summary = self.service.get_summary(self.user)

        self.assertEqual(summary["monthly_expense"], Decimal("0.00"))
