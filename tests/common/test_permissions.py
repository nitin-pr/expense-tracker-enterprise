from types import SimpleNamespace
from django.test import TestCase
from common.permissions import IsOwner


class IsOwnerTests(TestCase):
    """Unit tests for the IsOwner permission class.
    Tests the behavior of the has_object_permission method to ensure that it correctly
    allows access when the user matches the object's owner and denies access otherwise."""
    def setUp(self):
        self.permission = IsOwner()

    def test_allows_when_user_matches_object_owner(self):
        request = SimpleNamespace(user=SimpleNamespace(id=1))
        obj = SimpleNamespace(user_id=1)
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_denies_when_user_does_not_match_object_owner(self):
        request = SimpleNamespace(user=SimpleNamespace(id=1))
        obj = SimpleNamespace(user_id=2)
        self.assertFalse(self.permission.has_object_permission(request, None, obj))