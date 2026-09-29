from django.core.validators import RegexValidator
from django.db import models

from apps.accounts.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50)
    color = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message="Color must be a hex code like #4CAF50.",
            )
        ],
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="categories",
    )  # NULL = system default category, per DATABASE_DESIGN.md
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["created_by", "name"], name="uq_category_owner_name"
            ),
            # Plain UniqueConstraint above doesn't dedupe NULL created_by rows
            # (SQL treats every NULL as distinct) - this partial index closes
            # that gap for default categories specifically. See DATABASE_DESIGN.md.
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(created_by__isnull=True),
                name="uq_category_default_name",
            ),
        ]
        indexes = [
            models.Index(fields=["created_by"], name="idx_category_created_by"),
        ]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name
