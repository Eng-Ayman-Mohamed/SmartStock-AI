from core.base_repository import BaseRepository

from .models import PurchaseOrder


class PurchasingRepository(BaseRepository):
    def get_by_id(self, id: int):
        return PurchaseOrder.objects.get(pk=id)

    def get_all(self):
        return PurchaseOrder.objects.all()

    def create(self, data: dict):
        return PurchaseOrder.objects.create(**data)

    def update(self, id: int, data: dict):
        PurchaseOrder.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        PurchaseOrder.objects.filter(pk=id).delete()
