from django.db import models
from core.base_repository import BaseRepository
from .models import Product, SKU, StockLevel, SalesRecord


class InventoryRepository(BaseRepository):
    """Repository for Product model."""

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


class SKURepository(BaseRepository):
    """Repository for SKU model."""

    def get_by_id(self, id: int):
        return SKU.objects.select_related('product').get(pk=id)

    def get_all(self):
        return SKU.objects.select_related('product').all()

    def create(self, data: dict):
        return SKU.objects.create(**data)

    def update(self, id: int, data: dict):
        SKU.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        SKU.objects.filter(pk=id).delete()


class StockLevelRepository(BaseRepository):
    """Repository for StockLevel model."""

    def get_by_id(self, id: int):
        return StockLevel.objects.select_related('sku__product').get(pk=id)

    def get_all(self):
        return StockLevel.objects.select_related('sku__product').all()

    def create(self, data: dict):
        return StockLevel.objects.create(**data)

    def update(self, id: int, data: dict):
        StockLevel.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        StockLevel.objects.filter(pk=id).delete()

    def get_low_stock(self):
        """Return all stock levels where quantity is below reorder point."""
        return StockLevel.objects.select_related('sku__product').filter(
            quantity__lt=models.F('reorder_point')
        )


class SalesRecordRepository:
    """Repository for SalesRecord model (no delete/update needed)."""

    def get_by_sku(self, sku_id: int):
        return SalesRecord.objects.filter(sku_id=sku_id).order_by('date')

    def create(self, data: dict):
        return SalesRecord.objects.create(**data)

    def bulk_create(self, records: list):
        return SalesRecord.objects.bulk_create(
            [SalesRecord(**r) for r in records],
            ignore_conflicts=True
        )
