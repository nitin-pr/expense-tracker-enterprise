from rest_framework import serializers

from .models import Income


class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = ["id", "source", "amount", "income_date", "user", "created_at"]
        read_only_fields = ["id", "user", "created_at"]
