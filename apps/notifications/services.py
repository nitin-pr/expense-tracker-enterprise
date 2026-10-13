from common.services import BaseService

from apps.budgets.observers import BudgetObserver

from .channels import InAppNotificationChannel, NotificationDispatcher, compose_budget_threshold_message
from .repositories import NotificationRepository


class NotificationService(BaseService, BudgetObserver):
    """
    Public method signature (on_threshold_crossed) deliberately unchanged from
    Sprint 4, even though the internals now go through NotificationDispatcher/
    NotificationChannel instead of persisting directly - existing Sprint 4
    tests exercise this exact signature and keep passing unmodified.
    """

    def __init__(self, repository=None, dispatcher=None):
        super().__init__(repository or NotificationRepository())
        self.dispatcher = dispatcher or NotificationDispatcher([InAppNotificationChannel()])

    def on_threshold_crossed(self, user, budget, spent, percent, threshold_tier):
        title, message = compose_budget_threshold_message(budget, spent, percent, threshold_tier)
        self.dispatcher.dispatch(
            user, title, message, kind="budget_exceeded", budget=budget, threshold_tier=threshold_tier
        )

    def list_for_user(self, user):
        return self.repository.list(user=user)
