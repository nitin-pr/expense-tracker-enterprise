from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotFoundError

from .repositories import ExpenseRepository
from .serializers import ExpenseSerializer
from .services import ExpenseService


def get_service():
    return ExpenseService(repository=ExpenseRepository())


class ExpenseCreateView(APIView):
    """POST only, per US-014's AC - bare list/pagination is Sprint 3 (US-016/017/018)."""

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = get_service().create_expense(
            user=request.user,
            category=serializer.validated_data["category"],
            title=serializer.validated_data["title"],
            amount=serializer.validated_data["amount"],
            payment_method=serializer.validated_data["payment_method"],
            expense_date=serializer.validated_data["expense_date"],
            description=serializer.validated_data.get("description", ""),
            notes=serializer.validated_data.get("notes", ""),
            attachment=serializer.validated_data.get("attachment"),
        )
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)


class ExpenseDetailView(APIView):
    """
    Deliberately does NOT use common.permissions.IsOwner here. That permission
    raises a 403 for "exists but isn't yours" - correct for Category (visible to
    everyone via list), but wrong for Expense, which is never visible cross-user
    at all. Per the AC: "a non-existent or another user's expense ID returns 404,
    not 403 (no existence leakage)" - so both cases are deliberately folded into
    the same NotFoundError here, not split into 404 vs 403.
    """

    def get_object(self, pk, request):
        expense = get_service().get_expense(pk)
        if expense is None or expense.user_id != request.user.id:
            raise NotFoundError(f"Expense {pk} not found.")
        return expense

    def get(self, request, pk):
        expense = self.get_object(pk, request)
        return Response(ExpenseSerializer(expense).data)

    def put(self, request, pk):
        expense = self.get_object(pk, request)
        serializer = ExpenseSerializer(expense, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = get_service().update_expense(request.user, expense, **serializer.validated_data)
        return Response(ExpenseSerializer(updated).data)

    def delete(self, request, pk):
        expense = self.get_object(pk, request)
        get_service().delete_expense(expense)
        return Response(status=status.HTTP_204_NO_CONTENT)
