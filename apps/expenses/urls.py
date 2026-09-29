from django.urls import path

from .views import ExpenseCreateView, ExpenseDetailView

urlpatterns = [
    path("", ExpenseCreateView.as_view(), name="expense-create"),
    path("<int:pk>/", ExpenseDetailView.as_view(), name="expense-detail"),
]
