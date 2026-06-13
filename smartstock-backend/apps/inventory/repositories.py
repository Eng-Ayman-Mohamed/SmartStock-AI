from django.db import models, transaction

from core.base_repository import BaseRepository

from .models import SKU, Category, Product, SalesRecord, StockLevel, Supplier


class CategoryRepository(BaseRepository):
    """Repository for Category model."""

    def get_by_id(self, id: int):
        return Category.objects.get(pk=id)

    def get_all(self):
        return Category.objects.all()

    def create(self, data: dict):
        return Category.objects.create(**data)

    def update(self, id: int, data: dict):
        Category.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        Category.objects.filter(pk=id).delete()


class InventoryRepository(BaseRepository):
    """Repository for Product model."""

    def get_by_id(self, id: int):
        return Product.objects.select_related('category', 'supplier').prefetch_related(
            'skus__stock_level'
        ).get(pk=id)

    def get_all(self, include_inactive: bool = False):
        qs = Product.objects.select_related('category', 'supplier').prefetch_related(
            'skus__stock_level'
        )
        if not include_inactive:
            qs = qs.filter(is_active=True)
        return qs.all()

    def get_all_queryset(self, include_inactive: bool = False):
        qs = Product.objects.select_related('category', 'supplier').prefetch_related(
            'skus__stock_level'
        )
        if not include_inactive:
            qs = qs.filter(is_active=True)
        return qs.order_by('-created_at')

    def create(self, data: dict):
        return Product.objects.create(**data)

    def update(self, id: int, data: dict):
        Product.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def soft_delete(self, id: int):
        Product.objects.filter(pk=id).update(is_active=False)

    def delete(self, id: int):
        Product.objects.filter(pk=id).delete()

    def adjust_stock(self, stock_level_id: int, quantity_delta: int):
        with transaction.atomic():
            stock = StockLevel.objects.select_for_update().get(pk=stock_level_id)
            new_quantity = stock.quantity_on_hand + quantity_delta
            if new_quantity < stock.quantity_reserved:
                raise ValueError(
                    f'Cannot reduce stock to {new_quantity}: {stock.quantity_reserved} '
                    f'units are reserved (minimum allowed).'
                )
            stock.quantity_on_hand = new_quantity
            stock.save()
        return stock


class SKURepository(BaseRepository):
    """Repository for SKU model."""

    def get_by_id(self, id: int):
        return SKU.objects.select_related('product').get(pk=id)

    def get_by_code(self, code: str):
        return SKU.objects.select_related('product').filter(code=code).first()

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
        """Return all stock levels where quantity is at or below reorder point."""
        return (
            StockLevel.objects.select_related('sku__product', 'sku__product__supplier')
            .filter(quantity_on_hand__lte=models.F('reorder_point'))
            .order_by('quantity_on_hand')
        )

    def get_by_product_id(self, product_id: int):
        """Get the StockLevel for a given product_id. Returns None if not found."""
        sku = SKU.objects.filter(product_id=product_id).first()
        if not sku:
            return None
        try:
            return StockLevel.objects.select_related('sku__product__supplier').get(sku=sku)
        except StockLevel.DoesNotExist:
            return None

    def get_by_sku_id(self, sku_id: int):
        return StockLevel.objects.filter(sku_id=sku_id).first()


class SalesRecordRepository(BaseRepository):
    """Repository for SalesRecord model."""

    def get_by_id(self, id: int):
        return SalesRecord.objects.select_related('sku__product').get(pk=id)

    def get_all(self):
        return SalesRecord.objects.select_related('sku__product').all()

    def create(self, data: dict):
        return SalesRecord.objects.create(**data)

    def update(self, id: int, data: dict):
        SalesRecord.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        SalesRecord.objects.filter(pk=id).delete()

    def get_by_sku(self, sku_id: int):
        return SalesRecord.objects.filter(sku_id=sku_id).order_by('date')

    def bulk_create(self, records: list):
        return SalesRecord.objects.bulk_create(
            [SalesRecord(**r) for r in records], ignore_conflicts=True
        )


class SupplierRepository(BaseRepository):
    """Repository for Supplier model."""

    def get_by_id(self, id: int):
        return Supplier.objects.get(pk=id)

    def get_by_name(self, name: str):
        return Supplier.objects.filter(name__iexact=name).first()

    def get_all(self):
        return Supplier.objects.all()

    def create(self, data: dict):
        return Supplier.objects.create(**data)

    def update(self, id: int, data: dict):
        Supplier.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        Supplier.objects.filter(pk=id).delete()

    def soft_delete(self, id: int):
        Supplier.objects.filter(pk=id).update(is_active=False)
