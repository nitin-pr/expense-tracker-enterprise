from decimal import Decimal

from django.db.models import Sum

from common.repositories import BaseRepository

from .models import Income


class IncomeRepository(BaseRepository[Income]):
    model = Income

    def sum_for_period(self, user, date_from, date_to) -> Decimal:
        total = self.model.objects.filter(
            user=user, income_date__gte=date_from, income_date__lte=date_to
        ).aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0")
