import django_filters
from django.db import models as db_models

from .models import SKU, Product, SalesRecord, StockLevel


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.NumberFilter(field_name='category_id')
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    supplier = django_filters.NumberFilter(field_name='supplier_id')
    stock_status = django_filters.ChoiceFilter(
        choices=[
            ('in_stock', 'In Stock'),
            ('low_stock', 'Low Stock'),
            ('out_of_stock', 'Out of Stock'),
        ],
        method='filter_stock_status',
    )
    search = django_filters.CharFilter(method='filter_search')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'category_name',
            'supplier',
            'stock_status',
            'search',
            'created_after',
            'created_before',
        ]

    def filter_stock_status(self, queryset, name, value):
        from .services import InventoryService

        return InventoryService.filter_by_stock_status(queryset, value)

    def filter_search(self, queryset, name, value):
        return queryset.filter(db_models.Q(name__icontains=value) | db_models.Q(skus__code__icontains=value)).distinct()


class SKUFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(lookup_expr='icontains')
    product = django_filters.NumberFilter(field_name='product_id')

    class Meta:
        model = SKU
        fields = ['code', 'product']


class StockLevelFilter(django_filters.FilterSet):
    quantity_on_hand_lte = django_filters.NumberFilter(field_name='quantity_on_hand', lookup_expr='lte')
    quantity_on_hand_gte = django_filters.NumberFilter(field_name='quantity_on_hand', lookup_expr='gte')
    product = django_filters.NumberFilter(field_name='sku__product_id')

    class Meta:
        model = StockLevel
        fields = ['quantity_on_hand_lte', 'quantity_on_hand_gte', 'product']


class SalesRecordFilter(django_filters.FilterSet):
    date_after = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_before = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    sku = django_filters.NumberFilter(field_name='sku_id')
    quantity_sold_min = django_filters.NumberFilter(field_name='quantity_sold', lookup_expr='gte')

    class Meta:
        model = SalesRecord
        fields = ['date_after', 'date_before', 'sku', 'quantity_sold_min']
