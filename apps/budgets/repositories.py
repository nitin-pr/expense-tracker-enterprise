from common.repositories import BaseRepository

from .models import Budget


class BudgetRepository(BaseRepository[Budget]):
    model = Budget

    def get_for_period(self, user, month, year):
        # The UniqueConstraint(user, month, year) on the model doubles as the
        # index this lookup needs - no separate index required.
        return self.model.objects.filter(user=user, month=month, year=year).first()
