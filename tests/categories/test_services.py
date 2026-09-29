from django.test import TestCase

from apps.accounts.models import User
from apps.categories.repositories import CategoryRepository
from apps.categories.services import CategoryService
from common.exceptions import ValidationError


class CategoryServiceTests(TestCase):
    def setUp(self):
        self.service = CategoryService(repository=CategoryRepository())
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")

    def test_create_category_succeeds(self):
        category = self.service.create_category(self.user, "Groceries", "cart", "#4CAF50")
        self.assertEqual(category.name, "Groceries")
        self.assertEqual(category.created_by, self.user)

    def test_create_category_rejects_duplicate_name_for_same_user(self):
        self.service.create_category(self.user, "Groceries", "cart", "#4CAF50")

        with self.assertRaises(ValidationError):
            self.service.create_category(self.user, "Groceries", "cart2", "#000000")
