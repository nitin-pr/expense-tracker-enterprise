from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'

    def ready(self):
        # Observer registration: notifications subscribes to budgets, not the
        # other way around - matches Observer pattern semantics (the subscriber
        # registers itself with the subject). Safe regardless of INSTALLED_APPS
        # order: by the time any app's ready() runs, Django has already
        # populated every app's models (phase 1 of apps.populate()), so plain
        # module imports here are not an app-registry-timing risk.
        from apps.budgets.services import BudgetService

        from .services import NotificationService

        BudgetService.register_observer(NotificationService())
