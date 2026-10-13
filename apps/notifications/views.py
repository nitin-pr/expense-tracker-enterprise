from rest_framework.response import Response
from rest_framework.views import APIView

from .repositories import NotificationRepository
from .serializers import NotificationSerializer
from .services import NotificationService


class NotificationListView(APIView):
    def get(self, request):
        service = NotificationService(repository=NotificationRepository())
        notifications = service.list_for_user(request.user)
        return Response(NotificationSerializer(notifications, many=True).data)
