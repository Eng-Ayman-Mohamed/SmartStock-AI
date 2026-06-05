from core.base_repository import BaseRepository
from .models import Product


class InventoryRepository(BaseRepository):
    def get_by_id(self, id: int):
        return Product.objects.get(pk=id)

    def get_all(self):
        return Product.objects.all()

    def create(self, data: dict):
        return Product.objects.create(**data)

    def update(self, id: int, data: dict):
        Product.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        Product.objects.filter(pk=id).delete()
