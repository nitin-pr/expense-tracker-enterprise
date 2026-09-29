from unittest.mock import MagicMock

from django.test import TestCase
from firebase_admin.auth import InvalidIdTokenError
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from apps.accounts.authentication import FirebaseAuthentication
from apps.accounts.models import User


class FirebaseAuthenticationTests(TestCase):
    """Per US-007's AC: unit-tested with a mocked AuthProvider, not a real Firebase call."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.auth = FirebaseAuthentication()
        self.auth.auth_provider = MagicMock()

    def test_no_authorization_header_returns_none(self):
        request = self.factory.get("/api/auth/whoami/")
        self.assertIsNone(self.auth.authenticate(request))

    def test_non_bearer_header_returns_none(self):
        request = self.factory.get("/api/auth/whoami/", HTTP_AUTHORIZATION="Basic abc123")
        self.assertIsNone(self.auth.authenticate(request))

    def test_invalid_token_raises_authentication_failed(self):
        self.auth.auth_provider.verify_token.side_effect = InvalidIdTokenError("bad token")
        request = self.factory.get("/api/auth/whoami/", HTTP_AUTHORIZATION="Bearer badtoken")

        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_malformed_token_raises_authentication_failed(self):
        self.auth.auth_provider.verify_token.side_effect = ValueError("empty token")
        request = self.factory.get("/api/auth/whoami/", HTTP_AUTHORIZATION="Bearer ")

        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_valid_token_creates_and_returns_user(self):
        self.auth.auth_provider.verify_token.return_value = {
            "uid": "firebase-uid-123",
            "email": "newuser@example.com",
        }
        request = self.factory.get("/api/auth/whoami/", HTTP_AUTHORIZATION="Bearer validtoken")

        user, token = self.auth.authenticate(request)

        self.assertEqual(user.firebase_uid, "firebase-uid-123")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(token, "validtoken")
        self.assertTrue(User.objects.filter(firebase_uid="firebase-uid-123").exists())

    def test_valid_token_for_existing_user_does_not_duplicate(self):
        existing = User.objects.create(
            firebase_uid="existing-uid", email="existing@example.com", name="existing"
        )
        self.auth.auth_provider.verify_token.return_value = {
            "uid": "existing-uid",
            "email": "existing@example.com",
        }
        request = self.factory.get("/api/auth/whoami/", HTTP_AUTHORIZATION="Bearer validtoken")

        user, _ = self.auth.authenticate(request)

        self.assertEqual(User.objects.filter(firebase_uid="existing-uid").count(), 1)
        self.assertEqual(user.id, existing.id)

    def test_authenticate_header_is_bearer(self):
        request = self.factory.get("/api/auth/whoami/")
        self.assertEqual(self.auth.authenticate_header(request), "Bearer")
