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
