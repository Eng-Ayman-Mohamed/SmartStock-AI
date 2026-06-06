from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

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


class ProductViewSet(viewsets.ModelViewSet):
    """Full CRUD for products.
    
    - Viewer+: list, retrieve
    - Manager+: create, update
    - Admin: delete
    """
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

    def get_queryset(self):
        return InventoryService().get_all_products(self.request)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = InventoryService().create_product(serializer.validated_data)
        out = ProductSerializer(product, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        product = InventoryService().update_product(kwargs['pk'], serializer.validated_data)
        out = ProductSerializer(product, context={'request': request})
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        InventoryService().delete_product(kwargs['pk'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class SKUViewSet(viewsets.ModelViewSet):
    """Full CRUD for SKUs.
    
    - Viewer+: list, retrieve
    - Manager+: create, update
    - Admin: delete
    """
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

    def get_queryset(self):
        return SKUService().get_all_skus()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku = SKUService().create_sku(serializer.validated_data)
        out = SKUSerializer(sku, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        sku = SKUService().update_sku(kwargs['pk'], serializer.validated_data)
        out = SKUSerializer(sku, context={'request': request})
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        SKUService().delete_sku(kwargs['pk'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class StockLevelViewSet(viewsets.ModelViewSet):
    """CRUD for stock levels.
    
    - Viewer+: list, retrieve, low_stock
    - Manager+: update stock quantities
    """
    serializer_class = StockLevelSerializer
    filterset_class = StockLevelFilter
    search_fields = ['sku__code', 'sku__product__name']
    ordering_fields = ['quantity', 'updated_at']
    ordering = ['quantity']

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'low_stock'):
            return [IsViewerOrAbove()]
        return [IsManagerOrAbove()]

    def get_queryset(self):
        return InventoryService().get_all_stock_levels()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stock = InventoryService().create_stock_level(serializer.validated_data)
        out = StockLevelSerializer(stock, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        stock = InventoryService().update_stock_level(kwargs['pk'], serializer.validated_data)
        out = StockLevelSerializer(stock, context={'request': request})
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        InventoryService().delete_stock_level(kwargs['pk'])
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
    serializer_class = SalesRecordSerializer
    filterset_class = SalesRecordFilter
    search_fields = ['sku__code']
    ordering_fields = ['date', 'quantity_sold']
    ordering = ['-date']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        return [IsManagerOrAbove()]

    def get_queryset(self):
        return SalesRecordService().get_all_sales_records()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = SalesRecordService().create_sales_record(serializer.validated_data)
        out = SalesRecordSerializer(record, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        record = SalesRecordService().update_sales_record(kwargs['pk'], serializer.validated_data)
        out = SalesRecordSerializer(record, context={'request': request})
        return Response(out.data)

    def destroy(self, request, *args, **kwargs):
        SalesRecordService().delete_sales_record(kwargs['pk'])
        return Response(status=status.HTTP_204_NO_CONTENT)
