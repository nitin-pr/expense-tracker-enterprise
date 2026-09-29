from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.repositories import UserRepository


class UserRepositoryTests(TestCase):
    def setUp(self):
        self.repository = UserRepository()

    def test_get_by_firebase_uid_returns_none_when_missing(self):
        self.assertIsNone(self.repository.get_by_firebase_uid("does-not-exist"))

    def test_get_by_firebase_uid_returns_existing_user(self):
        user = User.objects.create(firebase_uid="uid-1", email="a@example.com", name="a")
        self.assertEqual(self.repository.get_by_firebase_uid("uid-1"), user)

    def test_get_or_create_by_firebase_uid_creates_new_user(self):
        user = self.repository.get_or_create_by_firebase_uid("uid-2", "new@example.com")

        self.assertEqual(user.firebase_uid, "uid-2")
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.name, "new")  # fallback from email prefix
        self.assertEqual(User.objects.count(), 1)

    def test_get_or_create_by_firebase_uid_returns_existing_user(self):
        existing = User.objects.create(firebase_uid="uid-3", email="existing@example.com", name="existing")

        user = self.repository.get_or_create_by_firebase_uid("uid-3", "existing@example.com")

        self.assertEqual(user.id, existing.id)
        self.assertEqual(User.objects.count(), 1)

    def test_inherited_crud_methods_work(self):
        # Proves BaseRepository's generic methods work correctly against a real model.
        created = self.repository.create(firebase_uid="uid-4", email="crud@example.com", name="crud")
        self.assertEqual(self.repository.get_by_id(created.id), created)

        updated = self.repository.update(created, name="updated-name")
        self.assertEqual(updated.name, "updated-name")

        self.repository.delete(updated)
        self.assertIsNone(self.repository.get_by_id(created.id))

    def test_update_rejects_unknown_field(self):
        user = User.objects.create(firebase_uid="uid-5", email="typo@example.com", name="typo")

        with self.assertRaises(AttributeError):
            self.repository.update(user, naem="oops")
