from apps.inventory.models import SKU
from core.base_repository import BaseRepository
from .models import ForecastResult


class ForecastingRepository(BaseRepository):
    def get_by_id(self, id: int):
        return ForecastResult.objects.get(pk=id)

    def get_all(self):
        return ForecastResult.objects.all()

    def get_by_sku(self, sku_id: int):
        return ForecastResult.objects.filter(sku_id=sku_id)

    def create(self, data: dict):
        return ForecastResult.objects.create(**data)

    def update(self, id: int, data: dict):
        ForecastResult.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        ForecastResult.objects.filter(pk=id).delete()

    def get_all_skus(self):
        return SKU.objects.all()
