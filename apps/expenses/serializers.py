from rest_framework import serializers

from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            "id", "title", "description", "amount", "category", "payment_method",
            "expense_date", "attachment", "notes", "user", "created_at", "updated_at",
        ]
        # user is never client-supplied - forced to request.user in the view/service.
        read_only_fields = ["id", "user", "created_at", "updated_at"]
