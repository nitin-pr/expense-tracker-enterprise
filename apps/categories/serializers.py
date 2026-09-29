from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "icon", "color", "created_by", "created_at"]
        # created_by is never client-supplied - set from request.user in the view,
        # same principle as Expense's ownership field later in this sprint.
        read_only_fields = ["id", "created_by", "created_at"]
