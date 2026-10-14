from rest_framework.response import Response
from rest_framework.views import APIView

from .repositories import NotificationRepository
from .serializers import NotificationSerializer
from .services import NotificationService


def get_service():
    return NotificationService(repository=NotificationRepository())


class NotificationListView(APIView):
    def get(self, request):
        notifications = get_service().list_for_user(request.user)
        return Response(NotificationSerializer(notifications, many=True).data)


class NotificationDetailView(APIView):
    """
    PATCH is the only write op - notifications are system-generated, so this
    exists purely to toggle `read` (US-030). Defaults to marking read since
    that's the only action the dashboard bell needs; passing {"read": false}
    allows marking back unread.
    """

    def get_object(self, pk, request):
        return get_service().get_for_user(request.user, pk)

    def patch(self, request, pk):
        notification = self.get_object(pk, request)
        read = request.data.get("read", True)
        updated = get_service().mark_read(notification, read=bool(read))
        return Response(NotificationSerializer(updated).data)
