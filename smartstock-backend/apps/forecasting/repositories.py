from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from apps.inventory.models import SKU, SalesRecord
from core.base_repository import BaseRepository

from .models import ForecastResult, ReorderFlag


class ForecastingRepository(BaseRepository):
    def get_by_id(self, id: int):
        return ForecastResult.objects.get(pk=id)

    def get_all(self):
        return ForecastResult.objects.all()

    def get_by_sku(self, sku_id: int):
        return ForecastResult.objects.filter(sku_id=sku_id).order_by('forecast_date')

    def get_by_sku_code_or_id(self, sku: str):
        filters = {'sku__code__iexact': sku}
        if str(sku).isdigit():
            filters = {'sku_id': int(sku)}
        return (
            ForecastResult.objects.filter(**filters)
            .select_related('sku__product')
            .order_by('forecast_date')[:30]
        )

    def get_next_for_product(self, product_id: int, forecast_days: int = 7):
        today = timezone.localdate()
        return (
            ForecastResult.objects.filter(
                sku__product_id=product_id,
                forecast_date__gte=today,
            )
            .select_related('sku')
            .order_by('forecast_date')[:forecast_days]
        )

    def create(self, data: dict):
        return ForecastResult.objects.create(**data)

    def update(self, id: int, data: dict):
        ForecastResult.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        ForecastResult.objects.filter(pk=id).delete()

    def get_all_skus(self):
        return SKU.objects.select_related('product').all()

    def get_sku(self, sku_id: int):
        return SKU.objects.get(pk=sku_id)

    def get_primary_sku_for_product(self, product_id: int):
        return SKU.objects.filter(product_id=product_id).order_by('id').first()

    def get_sku_by_code(self, sku_code: str):
        return SKU.objects.get(code=sku_code)

    def upsert_open_reorder_flag(self, sku_id: int, data: dict):
        flag, _ = ReorderFlag.objects.update_or_create(
            sku_id=sku_id,
            status=ReorderFlag.Status.OPEN,
            defaults=data,
        )
        return flag

    def get_sales_for_sku(self, sku_id: int):
        return SalesRecord.objects.filter(sku_id=sku_id).order_by('date')

    def get_sales_for_all_skus(self) -> dict[str, QuerySet]:
        """
        Returns {sku_code: SalesRecord queryset} for all active SKUs with sales data.
        Used by batch ingestion pipeline.
        """
        skus_with_sales = (
            SKU.objects.filter(sales_records__isnull=False, product__is_active=True)
            .distinct()
            .select_related('product')
            .values_list('id', 'code')
        )

        result = {}
        for sku_id, sku_code in skus_with_sales:
            result[sku_code] = self.get_sales_for_sku(sku_id)
        return result

    @transaction.atomic
    def upsert(
        self,
        sku_id: int,
        forecast_date: str,
        predicted_quantity: float,
        lower_bound: float = None,
        upper_bound: float = None,
        mae: float = None,
        mape: float = None,
        model_version: str = '',
    ):
        ForecastResult.objects.update_or_create(
            sku_id=sku_id,
            forecast_date=forecast_date,
            defaults={
                'predicted_quantity': predicted_quantity,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'mae': mae,
                'mape': mape,
                'model_version': model_version,
            },
        )
