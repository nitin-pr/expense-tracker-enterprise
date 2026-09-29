from django.test import TestCase

from apps.accounts.models import User
from apps.categories.models import Category
from apps.categories.repositories import CategoryRepository


class CategoryRepositoryTests(TestCase):
    def setUp(self):
        self.repository = CategoryRepository()
        self.user_a = User.objects.create(firebase_uid="uid-a", email="a@example.com", name="a")
        self.user_b = User.objects.create(firebase_uid="uid-b", email="b@example.com", name="b")
        # Note: "Food" etc. are already seeded by the 0002 data migration in every
        # test DB - using a distinct name here avoids colliding with real seed data.
        self.default_cat = Category.objects.create(created_by=None, name="Custom Default", icon="x", color="#111111")
        self.a_custom = Category.objects.create(created_by=self.user_a, name="Gym", icon="x", color="#222222")
        self.b_custom = Category.objects.create(created_by=self.user_b, name="Books", icon="x", color="#333333")

    def test_list_for_user_includes_defaults_and_own_only(self):
        # The 10 real seeded defaults (from the 0002 data migration) are also
        # legitimately present in every test DB - check membership, not exact
        # equality, since this test's own default_cat is one default among many.
        result = set(self.repository.list_for_user(self.user_a))
        self.assertIn(self.default_cat, result)
        self.assertIn(self.a_custom, result)
        self.assertNotIn(self.b_custom, result)
        self.assertEqual(len(result), 10 + 1 + 1)  # 10 seeded + this test's default + user_a's custom
