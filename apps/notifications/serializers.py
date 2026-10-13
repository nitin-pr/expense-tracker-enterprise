from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "kind", "threshold_tier", "read", "created_at"]
        read_only_fields = fields  # notifications are never created/edited via this API
