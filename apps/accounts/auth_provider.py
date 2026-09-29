from abc import ABC, abstractmethod
from firebase_admin import auth as firebase_auth

class AuthProvider(ABC):
    @abstractmethod
    def verify_token(self, id_token: str) -> dict:
        pass

class FirebaseAuthProvider(AuthProvider):
    def verify_token(self, id_token: str) -> dict:
        return firebase_auth.verify_id_token(id_token)