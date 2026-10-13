from decimal import Decimal
from unittest.mock import MagicMock

from django.test import TestCase

from apps.accounts.models import User
from apps.budgets.models import Budget
from apps.notifications.channels import (
    InAppNotificationChannel,
    NotificationChannel,
    NotificationDispatcher,
    compose_budget_threshold_message,
)
from apps.notifications.models import Notification


class InAppNotificationChannelTests(TestCase):
    def setUp(self):
        self.channel = InAppNotificationChannel()
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.budget = Budget.objects.create(user=self.user, month=1, year=2026, budget=Decimal("1000"))

    def test_send_persists_notification(self):
        self.channel.send(self.user, "title", "message", "budget_exceeded", budget=self.budget, threshold_tier=80)
        self.assertTrue(Notification.objects.filter(budget=self.budget, threshold_tier=80).exists())

    def test_send_twice_for_same_tier_does_not_raise_or_duplicate(self):
        self.channel.send(self.user, "t1", "m1", "budget_exceeded", budget=self.budget, threshold_tier=80)
        self.channel.send(self.user, "t2", "m2", "budget_exceeded", budget=self.budget, threshold_tier=80)
        self.assertEqual(Notification.objects.filter(budget=self.budget, threshold_tier=80).count(), 1)

    def test_send_without_budget_works_for_generic_notifications(self):
        self.channel.send(self.user, "Reminder", "Don't forget to log expenses", "daily_reminder")
        self.assertTrue(Notification.objects.filter(user=self.user, kind="daily_reminder").exists())


class NotificationDispatcherTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")

    def test_dispatch_calls_every_channel(self):
        channel_a = MagicMock(spec=NotificationChannel)
        channel_b = MagicMock(spec=NotificationChannel)
        dispatcher = NotificationDispatcher([channel_a, channel_b])

        dispatcher.dispatch(self.user, "title", "message", "budget_exceeded")

        channel_a.send.assert_called_once()
        channel_b.send.assert_called_once()

    def test_one_channel_failing_does_not_prevent_another_from_running(self):
        # Per US-027's AC: a threshold-crossing event always produces a
        # visible in-app notification even if other channels fail.
        failing_channel = MagicMock(spec=NotificationChannel)
        failing_channel.send.side_effect = RuntimeError("email server unreachable")
        working_channel = MagicMock(spec=NotificationChannel)
        dispatcher = NotificationDispatcher([failing_channel, working_channel])

        dispatcher.dispatch(self.user, "title", "message", "budget_exceeded")  # must not raise

        working_channel.send.assert_called_once()


class ComposeBudgetThresholdMessageTests(TestCase):
    def test_message_formats_amounts_with_two_decimal_places(self):
        user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        budget = Budget.objects.create(user=user, month=1, year=2026, budget=Decimal("1000"))

        title, message = compose_budget_threshold_message(budget, Decimal("850"), 85, 80)

        self.assertIn("850.00", message)
        self.assertIn("1000.00", message)
