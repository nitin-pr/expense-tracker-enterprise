from firebase_admin.auth import InvalidIdTokenError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .auth_provider import AuthProvider, FirebaseAuthProvider
from .repositories import UserRepository

class FirebaseAuthentication(BaseAuthentication):
    def __init__(self):
        self.auth_provider: AuthProvider = FirebaseAuthProvider()
        self.user_repository = UserRepository()

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization',"")
        if not auth_header.startswith('Bearer '):
            return None  # No authentication header provided

        token = auth_header.removeprefix("Bearer ").strip()

        try:
            claims = self.auth_provider.verify_token(token)
        except (ValueError, InvalidIdTokenError) as exc:
            raise AuthenticationFailed("Invalid or expired authentication token.") from exc

        user = self.user_repository.get_or_create_by_firebase_uid(
            firebase_uid=claims["uid"], email=claims.get("email", ""),
        )
        return (user, token)

    def authenticate_header(self, request):
        return "Bearer"