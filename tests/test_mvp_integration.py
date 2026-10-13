"""
Sprint 5's hardening/QA buffer, made concrete: SPRINT_PLAN.md calls out that
this sprint is "the first point every module is exercised together through
the Dashboard facade," where integration bugs are more likely to surface than
in earlier, more isolated per-story testing. This single test walks a
realistic MVP user journey through real HTTP requests against every module
built so far (accounts, categories, expenses, income, budgets, notifications,
dashboard) in one continuous flow, rather than each module's own test suite
exercising it in isolation.
"""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.categories.models import Category


class MVPUserJourneyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(firebase_uid="mvp-uid", email="mvp@example.com", name="mvp")
        self.other = User.objects.create(firebase_uid="other-uid", email="other@example.com", name="other")
        self.client.force_authenticate(user=self.user)

    def test_full_mvp_journey(self):
        today = date.today()

        # 1. A brand-new user sees the 10 seeded default categories.
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 10)
        food_category_id = next(c["id"] for c in response.data if c["name"] == "Food")

        # 2. Create a custom category.
        response = self.client.post(
            "/api/categories/", {"name": "Gym", "icon": "dumbbell", "color": "#4CAF50"}
        )
        self.assertEqual(response.status_code, 201)
        gym_category_id = response.data["id"]

        # 3. Set a monthly budget.
        response = self.client.post(
            "/api/budgets/", {"month": today.month, "year": today.year, "budget": "1000.00"}
        )
        self.assertEqual(response.status_code, 201)

        # 4. Record an expense against the custom category, under budget.
        response = self.client.post(
            "/api/expenses/",
            {
                "title": "Gym membership", "amount": "200.00", "category": gym_category_id,
                "payment_method": "card", "expense_date": str(today),
            },
        )
        self.assertEqual(response.status_code, 201)

        # 5. A second expense pushes spend to 85% - should cross the WARNING
        #    threshold and produce a real, visible in-app notification -
        #    exercising categories -> expenses -> budgets -> notifications
        #    in one continuous chain, not each tested against mocks.
        response = self.client.post(
            "/api/expenses/",
            {
                "title": "Groceries", "amount": "650.00", "category": food_category_id,
                "payment_method": "upi", "expense_date": str(today),
            },
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["kind"], "budget_exceeded")
        self.assertEqual(response.data[0]["threshold_tier"], 80)

        # 6. Record income.
        response = self.client.post(
            "/api/income/", {"source": "salary", "amount": "5000.00", "income_date": str(today)}
        )
        self.assertEqual(response.status_code, 201)

        # 7. Expense list search/filter/sort/pagination all work together
        #    against real data (not a dedicated fixture set).
        response = self.client.get("/api/expenses/?search=gym")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Gym membership")

        response = self.client.get(f"/api/expenses/?category={gym_category_id}")
        self.assertEqual(response.data["count"], 1)

        response = self.client.get("/api/expenses/?ordering=amount")
        amounts = [r["amount"] for r in response.data["results"]]
        self.assertEqual(amounts, sorted(amounts, key=Decimal))

        # 8. Budget status reflects both expenses.
        response = self.client.get(f"/api/budgets/?month={today.month}&year={today.year}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["spent"], Decimal("850.00"))
        self.assertEqual(response.data["remaining"], Decimal("150.00"))
        self.assertEqual(response.data["percent_used"], 85)

        # 9. The Dashboard facade aggregates everything correctly - the real
        #    point of this whole test. Cross-checks every number against
        #    what steps 1-8 actually did, not against a fresh assumption.
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["today_expense"], Decimal("850.00"))
        self.assertEqual(response.data["monthly_expense"], Decimal("850.00"))
        self.assertEqual(response.data["monthly_income"], Decimal("5000.00"))
        self.assertEqual(response.data["remaining_budget"], Decimal("150.00"))
        self.assertEqual(response.data["total_categories"], 11)  # 10 defaults + Gym

        # 10. US-013 integration: deleting a category still in use fails
        #     gracefully, end to end through the real HTTP API.
        response = self.client.delete(f"/api/categories/{gym_category_id}/")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Category.objects.filter(id=gym_category_id).exists())

        # 11. Cross-user isolation holds across every module, not just the
        #     one each module's own tests checked individually.
        #
        #     Note while writing this: /api/expenses/ returns a paginated
        #     envelope ({count, next, previous, results}, per US-018's
        #     explicit requirement), while /api/income/ and
        #     /api/notifications/ return bare lists - neither of those
        #     stories ever required pagination, so this is a deliberate,
        #     correct difference per-story, not a bug - but it does mean
        #     the API has genuinely different list-response shapes across
        #     endpoints, worth knowing before building a frontend against it.
        self.client.force_authenticate(user=self.other)

        response = self.client.get("/api/expenses/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0, "expenses leaked data across users")

        for path in ("/api/income/", "/api/notifications/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 0, f"{path} leaked data across users")

        other_dashboard = self.client.get("/api/dashboard/")
        self.assertEqual(other_dashboard.data["today_expense"], Decimal("0.00"))
        self.assertEqual(other_dashboard.data["total_categories"], 10)  # defaults only, no Gym
