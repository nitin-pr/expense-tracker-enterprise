from django.db.models import ProtectedError

from common.exceptions import ValidationError
from common.services import BaseService


class CategoryService(BaseService):
    def list_for_user(self, user):
        return self.repository.list_for_user(user)

    def create_category(self, user, name, icon, color):
        if self.repository.list(created_by=user, name=name).exists():
            raise ValidationError(f"You already have a category named '{name}'.")
        return self.repository.create(created_by=user, name=name, icon=icon, color=color)

    def delete_category(self, category):
        try:
            self.repository.delete(category)
        except ProtectedError as exc:
            # Surfaces the DB's ON DELETE RESTRICT as a clear 400, not a raw 500 -
            # per US-013's AC, a graceful surfacing of the constraint, not a bypass.
            raise ValidationError(
                "Cannot delete this category because it still has expenses assigned to it."
            ) from exc
