from django.db import models

from apps.accounts.models import User


class Budget(models.Model):
    month = models.SmallIntegerField()
    year = models.SmallIntegerField()
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "month", "year"], name="uq_budget_user_period"),
            models.CheckConstraint(check=models.Q(month__gte=1, month__lte=12), name="budget_month_valid"),
            models.CheckConstraint(check=models.Q(year__gte=2000, year__lte=2100), name="budget_year_valid"),
            models.CheckConstraint(check=models.Q(budget__gt=0), name="budget_amount_positive"),
        ]

    def __str__(self):
        return f"{self.user_id} {self.month}/{self.year}: {self.budget}"
