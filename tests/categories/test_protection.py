from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.categories.models import Category
from apps.categories.repositories import CategoryRepository
from apps.categories.services import CategoryService
from apps.expenses.models import Expense
from common.exceptions import ValidationError


class CategoryDeletionProtectionTests(TestCase):
    """
    US-013: a category with >=1 expense referencing it must not be deletable.
    This is the DB's ON DELETE RESTRICT (see Expense.category's on_delete),
    surfaced gracefully by CategoryService.delete_category rather than letting
    a raw RestrictedError become an unhandled 500.
    """

    def setUp(self):
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.category = Category.objects.create(
            created_by=self.user, name="Groceries", icon="cart", color="#4CAF50"
        )
        Expense.objects.create(
            title="Milk", amount=Decimal("3.00"), category=self.category,
            payment_method="cash", expense_date=date.today(), user=self.user,
        )

    def test_service_raises_validation_error_not_raw_db_exception(self):
        service = CategoryService(repository=CategoryRepository())
        with self.assertRaises(ValidationError):
            service.delete_category(self.category)
        # Confirms the delete was actually blocked, not silently no-op'd either.
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())

    def test_api_returns_clean_400_not_a_500(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.delete(f"/api/categories/{self.category.id}/")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())

    def test_category_with_no_expenses_still_deletes_normally(self):
        unused_category = Category.objects.create(
            created_by=self.user, name="Unused", icon="x", color="#000000"
        )
        service = CategoryService(repository=CategoryRepository())
        service.delete_category(unused_category)  # should not raise
        self.assertFalse(Category.objects.filter(id=unused_category.id).exists())
