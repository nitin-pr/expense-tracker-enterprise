from unittest.mock import patch

from django.test import TestCase
from firebase_admin.auth import InvalidIdTokenError
from rest_framework.test import APIClient

from apps.accounts.models import User


class WhoAmIViewTests(TestCase):
    """
    End-to-end proof of the full chain: request -> FirebaseAuthentication ->
    verified/created User -> view response. Only the Firebase SDK call itself
    is mocked (the one thing that needs real network access to Google); every
    other layer (URL routing, permission checks, the view, the ORM) runs for real.
    """

    def setUp(self):
        self.client = APIClient()

    @patch("apps.accounts.auth_provider.firebase_auth.verify_id_token")
    def test_valid_token_returns_user_info(self, mock_verify):
        mock_verify.return_value = {"uid": "whoami-uid", "email": "whoami@example.com"}

        response = self.client.get(
            "/api/auth/whoami/", HTTP_AUTHORIZATION="Bearer sometoken"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "whoami@example.com")
        self.assertEqual(response.data["firebase_uid"], "whoami-uid")
        self.assertTrue(User.objects.filter(firebase_uid="whoami-uid").exists())

    def test_missing_token_returns_401(self):
        response = self.client.get("/api/auth/whoami/")
        self.assertEqual(response.status_code, 401)

    @patch("apps.accounts.auth_provider.firebase_auth.verify_id_token")
    def test_invalid_token_returns_401(self, mock_verify):
        mock_verify.side_effect = InvalidIdTokenError("bad token")

        response = self.client.get(
            "/api/auth/whoami/", HTTP_AUTHORIZATION="Bearer badtoken"
        )

        self.assertEqual(response.status_code, 401)
