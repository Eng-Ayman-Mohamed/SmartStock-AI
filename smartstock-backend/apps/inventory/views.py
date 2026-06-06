from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.authentication.permissions import IsViewerOrAbove, IsManagerOrAbove, IsAdminOnly, ReadOnly
from .filters import ProductFilter, SKUFilter, StockLevelFilter
from .models import Product, SKU, StockLevel, SalesRecord ,Supplier
from .serializers import (
    ProductSerializer,
    ProductWriteSerializer,
    SKUSerializer,
    StockLevelSerializer,
    SalesRecordSerializer,
    SupplierSerializer,
)
from .services import InventoryService


class ProductViewSet(viewsets.ModelViewSet):
    """Full CRUD for products.
    
    - Viewer+: list, retrieve
    - Manager+: create, update
    - Admin: delete
    """
    queryset = Product.objects.prefetch_related('skus').all()
    filterset_class = ProductFilter
    search_fields = ['name', 'category']
    ordering_fields = ['name', 'category', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ProductWriteSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        if self.action in ('create', 'update', 'partial_update'):
            return [IsManagerOrAbove()]
        if self.action == 'destroy':
            return [IsAdminOnly()]
        return [IsManagerOrAbove()]


class SKUViewSet(viewsets.ModelViewSet):
    """Full CRUD for SKUs.
    
    - Viewer+: list, retrieve
    - Manager+: create, update
    - Admin: delete
    """
    queryset = SKU.objects.select_related('product').all()
    serializer_class = SKUSerializer
    filterset_class = SKUFilter
    search_fields = ['code', 'product__name']
    ordering_fields = ['code', 'created_at']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        if self.action in ('create', 'update', 'partial_update'):
            return [IsManagerOrAbove()]
        if self.action == 'destroy':
            return [IsAdminOnly()]
        return [IsManagerOrAbove()]


class StockLevelViewSet(viewsets.ModelViewSet):
    """CRUD for stock levels.
    
    - Viewer+: list, retrieve
    - Manager+: update stock quantities
    """
    queryset = StockLevel.objects.select_related('sku__product').all()
    serializer_class = StockLevelSerializer
    filterset_class = StockLevelFilter
    search_fields = ['sku__code', 'sku__product__name']
    ordering_fields = ['quantity', 'updated_at']
    ordering = ['quantity']

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'low_stock'):
            return [IsViewerOrAbove()]
        return [IsManagerOrAbove()]

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Return items where quantity < reorder_point (cached)."""
        items = InventoryService().get_low_stock_items()
        return Response(items)


class SalesRecordViewSet(viewsets.ModelViewSet):
    """CRUD for sales records (training data for Prophet).
    
    - Viewer+: list, retrieve
    - Manager+: create, update, delete
    """
    queryset = SalesRecord.objects.select_related('sku__product').all()
    serializer_class = SalesRecordSerializer
    search_fields = ['sku__code']
    ordering_fields = ['date', 'quantity_sold']
    ordering = ['-date']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        return [IsManagerOrAbove()]


class SupplierViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for suppliers.
    - Viewer+: list, retrieve
    - Manager+: create, update
    - Admin: delete (soft delete via is_active)
    """
    queryset = Supplier.objects.filter(is_active=True).order_by('name')
    serializer_class = SupplierSerializer
    search_fields = ['name', 'contact_email']
    ordering_fields = ['name', 'created_at']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        if self.action in ('create', 'update', 'partial_update'):
            return [IsManagerOrAbove()]
        if self.action == 'destroy':
            return [IsAdminOnly()]
        return [IsManagerOrAbove()]

    def perform_destroy(self, instance):
        # Soft delete: matches blueprint's is_active pattern
        instance.is_active = False
        instance.save()