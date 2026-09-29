from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.categories.models import Category


class CategoryViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(firebase_uid="uid-1", email="u@example.com", name="u")
        self.other = User.objects.create(firebase_uid="uid-2", email="o@example.com", name="o")
        self.client.force_authenticate(user=self.user)

    def test_list_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, 401)

    def test_list_includes_seeded_defaults(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, 200)
        names = {c["name"] for c in response.data}
        self.assertIn("Food", names)
        self.assertIn("Salary", names)
        self.assertEqual(len(response.data), 10)  # exactly the 10 seeded defaults, nothing else yet

    def test_create_category_success(self):
        response = self.client.post(
            "/api/categories/", {"name": "Gym", "icon": "dumbbell", "color": "#4CAF50"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "Gym")
        # created_by is never client-supplied - confirm it's forced to request.user regardless of input
        self.assertEqual(Category.objects.get(name="Gym").created_by, self.user)

    def test_create_category_rejects_invalid_color(self):
        response = self.client.post(
            "/api/categories/", {"name": "Gym", "icon": "dumbbell", "color": "not-a-color"}
        )
        self.assertEqual(response.status_code, 400)

    def test_create_category_rejects_duplicate_name_for_same_user(self):
        self.client.post("/api/categories/", {"name": "Gym", "icon": "x", "color": "#111111"})
        response = self.client.post("/api/categories/", {"name": "Gym", "icon": "y", "color": "#222222"})
        self.assertEqual(response.status_code, 400)

    def test_delete_default_category_is_forbidden(self):
        default_cat = Category.objects.get(name="Food", created_by=None)
        response = self.client.delete(f"/api/categories/{default_cat.id}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Category.objects.filter(id=default_cat.id).exists())

    def test_delete_another_users_category_is_forbidden(self):
        other_cat = Category.objects.create(created_by=self.other, name="Private", icon="x", color="#111111")
        response = self.client.delete(f"/api/categories/{other_cat.id}/")
        self.assertEqual(response.status_code, 403)

    def test_delete_own_category_succeeds(self):
        own_cat = Category.objects.create(created_by=self.user, name="Mine", icon="x", color="#111111")
        response = self.client.delete(f"/api/categories/{own_cat.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Category.objects.filter(id=own_cat.id).exists())

    def test_delete_nonexistent_category_returns_404(self):
        response = self.client.delete("/api/categories/999999/")
        self.assertEqual(response.status_code, 404)
