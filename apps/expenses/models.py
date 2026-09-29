from django.db import models

from apps.accounts.models import User
from apps.categories.models import Category
from common.constants import PaymentMethod


class Expense(models.Model):
    title = models.CharField(max_length=200)
    # description/notes: DATABASE_DESIGN.md allows NULL, but Django convention
    # prefers empty string over NULL for text fields (avoids two ways to
    # represent "no data") - blank=True + default="" instead of null=True.
    description = models.TextField(blank=True, default="")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.RESTRICT, related_name="expenses")
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    expense_date = models.DateField()
    # FileField genuinely needs null=True (unlike Char/TextField) - empty
    # string isn't a meaningful "no file" sentinel here.
    attachment = models.FileField(upload_to="receipts/", blank=True, null=True)
    notes = models.TextField(blank=True, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gt=0), name="expense_amount_positive"),
            models.CheckConstraint(
                check=models.Q(payment_method__in=PaymentMethod.values),
                name="expense_payment_method_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-expense_date"], name="idx_expense_user_date"),
            models.Index(fields=["user", "category"], name="idx_expense_user_category"),
            models.Index(fields=["user", "payment_method"], name="idx_expense_user_payment"),
        ]
        ordering = ["-expense_date"]

    def __str__(self):
        return f"{self.title} ({self.amount})"
