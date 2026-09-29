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
        valid_fields = {f.name for f in instance._meta.get_fields()}
        for attr, value in data.items():
            if attr not in valid_fields:
                raise AttributeError(
                    f"{type(instance).__name__} has no field '{attr}'"
                )
            setattr(instance, attr, value)
        instance.save()
        return instance

    def delete(self, instance: T) -> None:
        instance.delete()
        