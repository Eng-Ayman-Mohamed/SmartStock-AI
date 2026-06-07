from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated

from apps.authentication.permissions import IsViewerOrAbove, IsManagerOrAbove, IsAdminOnly
from .filters import ProductFilter, SKUFilter, StockLevelFilter, SalesRecordFilter
from .serializers import (
    ProductSerializer,
    ProductWriteSerializer,
    SKUSerializer,
    StockLevelSerializer,
    SalesRecordSerializer,
    SupplierSerializer,
)
from .services import InventoryService, SKUService, SalesRecordService
from .models import Product, SKU, StockLevel, SalesRecord


class ProductViewSet(viewsets.ModelViewSet):
    """Full CRUD for products.
    
    - Viewer+: list, retrieve
    - Manager+: create, update
    - Admin: delete
    """
    permission_classes = [IsAuthenticated]
    queryset = Product.objects.prefetch_related('skus').all().order_by('-created_at')
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

    def _invalidate_product_cache(self):
        cache.delete_pattern('product_list_*')

    def list(self, request, *args, **kwargs):
        cache_key = f"product_list_{request.get_full_path()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        return response

    def perform_create(self, serializer):
        product = InventoryService().create_product(serializer.validated_data)
        self._invalidate_product_cache()
        return product

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = self.perform_create(serializer)
        out = ProductSerializer(product, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        product = InventoryService().update_product(
            serializer.instance.id, serializer.validated_data,
        )
        self._invalidate_product_cache()
        return product

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        product = self.perform_update(serializer)
        out = ProductSerializer(product, context={'request': request})
        return Response(out.data)

    def perform_destroy(self, instance):
        InventoryService().delete_product(instance.id)
        self._invalidate_product_cache()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SKUViewSet(viewsets.ModelViewSet):
    """Full CRUD for SKUs.
    
    - Viewer+: list, retrieve
    - Manager+: create, update
    - Admin: delete
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SKUSerializer
    filterset_class = SKUFilter
    search_fields = ['code', 'product__name']
    ordering_fields = ['code', 'created_at']
    ordering = ['-created_at']
    queryset = SKU.objects.select_related('product').all().order_by('-created_at')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        if self.action in ('create', 'update', 'partial_update'):
            return [IsManagerOrAbove()]
        if self.action == 'destroy':
            return [IsAdminOnly()]
        return [IsManagerOrAbove()]

    def perform_create(self, serializer):
        return SKUService().create_sku(serializer.validated_data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku = self.perform_create(serializer)
        out = SKUSerializer(sku, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        return SKUService().update_sku(
            serializer.instance.id, serializer.validated_data,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        sku = self.perform_update(serializer)
        out = SKUSerializer(sku, context={'request': request})
        return Response(out.data)

    def perform_destroy(self, instance):
        SKUService().delete_sku(instance.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class StockLevelViewSet(viewsets.ModelViewSet):
    """CRUD for stock levels.
    
    - Viewer+: list, retrieve, low_stock
    - Manager+: update stock quantities
    """
    permission_classes = [IsAuthenticated]
    serializer_class = StockLevelSerializer
    filterset_class = StockLevelFilter
    search_fields = ['sku__code', 'sku__product__name']
    ordering_fields = ['quantity', 'updated_at']
    ordering = ['quantity']
    queryset = StockLevel.objects.select_related('sku__product').all().order_by('sku__code')

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'low_stock'):
            return [IsViewerOrAbove()]
        return [IsManagerOrAbove()]

    def perform_create(self, serializer):
        return InventoryService().create_stock_level(serializer.validated_data)

    def perform_update(self, serializer):
        return InventoryService().update_stock_level(
            serializer.instance.id, serializer.validated_data,
        )

    def perform_destroy(self, instance):
        InventoryService().delete_stock_level(instance.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stock = self.perform_create(serializer)
        out = StockLevelSerializer(stock, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        stock = self.perform_update(serializer)
        out = StockLevelSerializer(stock, context={'request': request})
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

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
    permission_classes = [IsAuthenticated]
    serializer_class = SalesRecordSerializer
    filterset_class = SalesRecordFilter
    search_fields = ['sku__code']
    ordering_fields = ['date', 'quantity_sold']
    ordering = ['-date']
    queryset = SalesRecord.objects.select_related('sku__product').all().order_by('-date')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        return [IsManagerOrAbove()]

    def perform_create(self, serializer):
        return SalesRecordService().create_sales_record(serializer.validated_data)

    def perform_update(self, serializer):
        return SalesRecordService().update_sales_record(
            serializer.instance.id, serializer.validated_data,
        )

    def perform_destroy(self, instance):
        SalesRecordService().delete_sales_record(instance.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = self.perform_create(serializer)
        out = SalesRecordSerializer(record, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        record = self.perform_update(serializer)
        out = SalesRecordSerializer(record, context={'request': request})
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
