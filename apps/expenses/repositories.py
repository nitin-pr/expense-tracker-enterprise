from decimal import Decimal

from django.db.models import Q, QuerySet, Sum

from common.repositories import BaseRepository

from .models import Expense


class ExpenseRepository(BaseRepository[Expense]):
    model = Expense

    def list_filtered(self, user, filters) -> QuerySet[Expense]:
        queryset = self.model.objects.filter(user=user)

        if filters.search:
            queryset = queryset.filter(
                Q(title__icontains=filters.search) | Q(description__icontains=filters.search)
            )
        if filters.category_id is not None:
            queryset = queryset.filter(category_id=filters.category_id)
        if filters.date_from is not None:
            queryset = queryset.filter(expense_date__gte=filters.date_from)
        if filters.date_to is not None:
            queryset = queryset.filter(expense_date__lte=filters.date_to)
        if filters.amount_min is not None:
            queryset = queryset.filter(amount__gte=filters.amount_min)
        if filters.amount_max is not None:
            queryset = queryset.filter(amount__lte=filters.amount_max)
        if filters.payment_method:
            queryset = queryset.filter(payment_method=filters.payment_method)

        return queryset.order_by(filters.ordering)

    def sum_for_period(self, user, date_from, date_to) -> Decimal:
        total = self.model.objects.filter(
            user=user, expense_date__gte=date_from, expense_date__lte=date_to
        ).aggregate(total=Sum("amount"))["total"]
        return total or Decimal("0")
