from typing import Generic, TypeVar, Optional, Type
from django.db.models import Model, QuerySet

T = TypeVar("T", bound=Model)

class BaseRepository(Generic[T]):
    model: Type[T]

    def get_by_id(self, id: int) -> Optional[T]:
        return self.model.objects.filter(id=id).first()

    def list(self,**filters) -> QuerySet[T]:
        return self.model.objects.filter(**filters)

    def create(self, **data) -> T:
        return self.model.objects.create(**data)

    def update(self, instance: T, **data) -> T:
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def delete(self, instance: T) -> None:
        instance.delete()
        