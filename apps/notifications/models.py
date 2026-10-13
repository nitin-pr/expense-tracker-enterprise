from django.db import models

from apps.accounts.models import User
from apps.budgets.models import Budget

NOTIFICATION_KINDS = ["budget_exceeded", "budget_reminder", "daily_reminder"]
THRESHOLD_TIERS = [80, 90, 100]


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    budget = models.ForeignKey(
        Budget, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications"
    )
    threshold_tier = models.SmallIntegerField(null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    kind = models.CharField(max_length=30, choices=[(k, k) for k in NOTIFICATION_KINDS])
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # budget_id + threshold_tier together are the idempotency backstop for
            # US-026's race-safety: NULLs are distinct in SQL, so this plain
            # UniqueConstraint correctly does NOT constrain non-budget notifications
            # (daily_reminder etc., budget=NULL) against each other - unlike
            # Category's default-name case, no partial index is needed here.
            models.UniqueConstraint(fields=["budget", "threshold_tier"], name="uq_budget_threshold_once"),
            models.CheckConstraint(
                check=models.Q(threshold_tier__in=THRESHOLD_TIERS) | models.Q(threshold_tier__isnull=True),
                name="notification_threshold_tier_valid",
            ),
            models.CheckConstraint(
                check=models.Q(kind__in=NOTIFICATION_KINDS), name="notification_kind_valid"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "read", "-created_at"], name="idx_notification_user_read"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
