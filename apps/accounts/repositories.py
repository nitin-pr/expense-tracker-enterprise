from typing import Optional

from common.repositories import BaseRepository
from .models import User

class UserRepository(BaseRepository[User]):
    model = User

    def get_by_firebase_uid(self, uid: str) -> Optional[User]:
        return self.model.objects.filter(firebase_uid=uid).first() 

    def get_or_create_by_firebase_uid(self, firebase_uid: str, email: str) -> User:
        user, created = self.model.objects.get_or_create(
            firebase_uid=firebase_uid,
            defaults={'email': email, "name": email.split('@')[0]}
        )
        return user 