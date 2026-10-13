from datetime import date
from decimal import Decimal

from apps.budgets.repositories import BudgetRepository
from apps.budgets.services import BudgetService
from apps.categories.repositories import CategoryRepository
from apps.categories.services import CategoryService
from apps.expenses.repositories import ExpenseRepository
from apps.expenses.services import ExpenseService
from apps.income.repositories import IncomeRepository
from apps.income.services import IncomeService
from common.exceptions import NotFoundError

_CENTS = Decimal("0.01")


class DashboardService:
    """
    Facade (LLD S9): the one place aggregation across domain modules is
    allowed to live, specifically so expenses/income/budgets/categories
    never need to know about each other or about Dashboard's existence.
    One GET /api/dashboard/ call replaces four separate frontend requests.

    Scoped exactly to US-031's AC: today's expense, monthly expense/income,
    remaining budget, total categories. Recent transactions (US-032) and
    charts (US-033) are separate, later Sprint 7 stories - not built here.
    """

    def __init__(self, expense_service=None, income_service=None, budget_service=None, category_service=None):
        self.expense_service = expense_service or ExpenseService(repository=ExpenseRepository())
        self.income_service = income_service or IncomeService(repository=IncomeRepository())
        self.budget_service = budget_service or BudgetService(repository=BudgetRepository())
        self.category_service = category_service or CategoryService(repository=CategoryRepository())

    def get_summary(self, user):
        today = date.today()

        remaining_budget = None
        try:
            status = self.budget_service.get_status(user, today.month, today.year)
            remaining_budget = status["remaining"]
        except NotFoundError:
            # Correct for a brand-new user (or any month with no budget set):
            # None (no budget exists to compute "remaining" from) rather than
            # 0, which would misleadingly read as "you've spent your entire
            # $0 budget." The whole dashboard must stay a 200, not propagate
            # the 404 from a single missing sub-resource.
            pass

        return {
            "today_expense": self.expense_service.get_today_total(user).quantize(_CENTS),
            "monthly_expense": self.expense_service.get_monthly_total(user, today.month, today.year).quantize(_CENTS),
            "monthly_income": self.income_service.get_monthly_total(user, today.month, today.year).quantize(_CENTS),
            "remaining_budget": remaining_budget,  # already quantized by BudgetService.get_status, or None
            "total_categories": self.category_service.list_for_user(user).count(),
        }
