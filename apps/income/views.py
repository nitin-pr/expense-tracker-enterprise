from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotFoundError

from .repositories import IncomeRepository
from .serializers import IncomeSerializer
from .services import IncomeService


def get_service():
    return IncomeService(repository=IncomeRepository())


class IncomeListCreateView(APIView):
    def get(self, request):
        entries = get_service().repository.list(user=request.user)
        return Response(IncomeSerializer(entries, many=True).data)

    def post(self, request):
        serializer = IncomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        income = get_service().create_income(
            user=request.user,
            source=serializer.validated_data["source"],
            amount=serializer.validated_data["amount"],
            income_date=serializer.validated_data["income_date"],
        )
        return Response(IncomeSerializer(income).data, status=status.HTTP_201_CREATED)


class IncomeDetailView(APIView):
    """Same 404-not-403 reasoning as ExpenseDetailView - income is never visible cross-user."""

    def get_object(self, pk, request):
        income = get_service().get_income(pk)
        if income is None or income.user_id != request.user.id:
            raise NotFoundError(f"Income entry {pk} not found.")
        return income

    def get(self, request, pk):
        income = self.get_object(pk, request)
        return Response(IncomeSerializer(income).data)

    def put(self, request, pk):
        income = self.get_object(pk, request)
        serializer = IncomeSerializer(income, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = get_service().update_income(income, **serializer.validated_data)
        return Response(IncomeSerializer(updated).data)

    def delete(self, request, pk):
        income = self.get_object(pk, request)
        get_service().delete_income(income)
        return Response(status=status.HTTP_204_NO_CONTENT)
