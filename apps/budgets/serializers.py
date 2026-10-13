from rest_framework import serializers

from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["id", "month", "year", "budget", "user", "created_at"]
        read_only_fields = ["id", "user", "created_at"]
