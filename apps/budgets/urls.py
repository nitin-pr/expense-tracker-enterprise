from django.urls import path

from .views import BudgetDetailView, BudgetListCreateView

urlpatterns = [
    path("", BudgetListCreateView.as_view(), name="budget-list-create"),
    path("<int:pk>/", BudgetDetailView.as_view(), name="budget-detail"),
]
