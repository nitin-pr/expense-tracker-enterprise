from common.repositories import BaseRepository

from .models import Notification


class NotificationRepository(BaseRepository[Notification]):
    model = Notification
