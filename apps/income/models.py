from django.db import models

from apps.accounts.models import User
from common.constants import IncomeSource


class Income(models.Model):
    source = models.CharField(max_length=20, choices=IncomeSource.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    income_date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="income_entries")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name="income_amount_positive"),
            models.CheckConstraint(
                check=models.Q(source__in=IncomeSource.values), name="income_source_valid"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-income_date"], name="idx_income_user_date"),
        ]
        ordering = ["-income_date"]

    def __str__(self):
        return f"{self.source} ({self.amount})"
