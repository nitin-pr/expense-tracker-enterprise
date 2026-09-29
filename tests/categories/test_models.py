from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.accounts.models import User
from apps.categories.models import Category


class CategoryModelConstraintTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create(firebase_uid="uid-a", email="a@example.com", name="a")
        self.user_b = User.objects.create(firebase_uid="uid-b", email="b@example.com", name="b")

    def test_two_different_users_can_have_same_category_name(self):
        Category.objects.create(created_by=self.user_a, name="Snacks", icon="x", color="#111111")
        Category.objects.create(created_by=self.user_b, name="Snacks", icon="x", color="#111111")
        self.assertEqual(Category.objects.filter(name="Snacks").count(), 2)

    def test_same_user_cannot_duplicate_category_name(self):
        Category.objects.create(created_by=self.user_a, name="Snacks", icon="x", color="#111111")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(created_by=self.user_a, name="Snacks", icon="y", color="#222222")

    def test_two_default_categories_cannot_share_a_name(self):
        # This is exactly the gap a plain UniqueConstraint(created_by, name) misses -
        # NULLs are distinct in SQL, so without the partial index this would succeed.
        Category.objects.create(created_by=None, name="Misc", icon="x", color="#111111")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(created_by=None, name="Misc", icon="y", color="#222222")
