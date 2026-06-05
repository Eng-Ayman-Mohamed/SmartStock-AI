import django_filters
from .models import Product, SKU, StockLevel


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.CharFilter(lookup_expr='iexact')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['name', 'category', 'created_after', 'created_before']


class SKUFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(lookup_expr='icontains')
    product = django_filters.NumberFilter(field_name='product_id')

    class Meta:
        model = SKU
        fields = ['code', 'product']


class StockLevelFilter(django_filters.FilterSet):
    quantity_lte = django_filters.NumberFilter(field_name='quantity', lookup_expr='lte')
    quantity_gte = django_filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    product = django_filters.NumberFilter(field_name='sku__product_id')

    class Meta:
        model = StockLevel
        fields = ['quantity_lte', 'quantity_gte', 'product']
