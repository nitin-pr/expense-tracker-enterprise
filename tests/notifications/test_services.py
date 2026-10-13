from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.budgets.models import Budget
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.service = NotificationService()
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.budget = Budget.objects.create(user=self.user, month=1, year=2026, budget=Decimal("1000"))

    def test_on_threshold_crossed_creates_notification(self):
        self.service.on_threshold_crossed(self.user, self.budget, Decimal("850"), 85, 80)
        notification = Notification.objects.get(budget=self.budget, threshold_tier=80)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.kind, "budget_exceeded")

    def test_on_threshold_crossed_twice_for_same_tier_does_not_raise_or_duplicate(self):
        self.service.on_threshold_crossed(self.user, self.budget, Decimal("850"), 85, 80)
        self.service.on_threshold_crossed(self.user, self.budget, Decimal("860"), 86, 80)  # should not raise

        self.assertEqual(Notification.objects.filter(budget=self.budget, threshold_tier=80).count(), 1)

    def test_different_tiers_for_same_budget_both_persist(self):
        self.service.on_threshold_crossed(self.user, self.budget, Decimal("850"), 85, 80)
        self.service.on_threshold_crossed(self.user, self.budget, Decimal("950"), 95, 90)

        self.assertEqual(Notification.objects.filter(budget=self.budget).count(), 2)
