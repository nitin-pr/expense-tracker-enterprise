from django.db.models import Q, QuerySet

from common.repositories import BaseRepository

from .models import Category


class CategoryRepository(BaseRepository[Category]):
    model = Category

    def list_for_user(self, user) -> QuerySet[Category]:
        """Defaults (created_by IS NULL) union the user's own custom categories."""
        return self.model.objects.filter(Q(created_by__isnull=True) | Q(created_by=user))
