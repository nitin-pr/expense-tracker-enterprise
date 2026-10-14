from datetime import date

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ValidationError

from .repositories import BudgetRepository
from .serializers import BudgetSerializer
from .services import BudgetService


def get_service():
    return BudgetService(repository=BudgetRepository())


class BudgetListCreateView(APIView):
    def get(self, request):
        today = date.today()
        try:
            month = int(request.query_params.get("month", today.month))
            year = int(request.query_params.get("year", today.year))
        except ValueError:
            raise ValidationError("'month' and 'year' must be valid integers.")
        return Response(get_service().get_status(request.user, month, year))

    def post(self, request):
        serializer = BudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        budget = get_service().create_budget(
            request.user,
            serializer.validated_data["month"],
            serializer.validated_data["year"],
            serializer.validated_data["budget"],
        )
        return Response(BudgetSerializer(budget).data, status=status.HTTP_201_CREATED)


class BudgetDetailView(APIView):
    """
    Deliberately folds "not found" and "not yours" into the same 404, same
    reasoning as ExpenseDetailView - a budget is never visible cross-user.
    """

    def get_object(self, pk, request):
        return get_service().get_budget_for_user(request.user, pk)

    def get(self, request, pk):
        budget = self.get_object(pk, request)
        return Response(get_service().get_status_for_budget(budget))

    def put(self, request, pk):
        # Amount only - month/year are not accepted here, see BudgetService.update_budget.
        budget = self.get_object(pk, request)
        serializer = BudgetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if "budget" not in serializer.validated_data:
            raise ValidationError("'budget' is required.")
        updated = get_service().update_budget(budget, serializer.validated_data["budget"])
        return Response(get_service().get_status_for_budget(updated))

    def delete(self, request, pk):
        budget = self.get_object(pk, request)
        get_service().delete_budget(budget)
        return Response(status=status.HTTP_204_NO_CONTENT)
