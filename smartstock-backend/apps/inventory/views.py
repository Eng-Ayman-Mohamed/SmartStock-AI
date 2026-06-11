import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from django.core.cache import cache
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ai.llm.schemas import NLQueryFilters
from apps.audit.models import AuditLog
from apps.authentication.permissions import IsAdminOnly, IsManagerOrAbove, IsViewerOrAbove
from apps.forecasting.services import ForecastingService
from config.schema_serializers import ErrorResponseSerializer, ValidationErrorResponseSerializer

from .filters import ProductFilter, SalesRecordFilter, SKUFilter, StockLevelFilter
from .models import SKU, Category, Product, SalesRecord, StockLevel, Supplier
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductWriteSerializer,
    SalesRecordSerializer,
    SKUSerializer,
    StockLevelSerializer,
    SupplierSerializer,
)
from .services import InventoryService, SalesRecordService, SKUService

_nl_chain = None
_langfuse_client = None


def get_nl_chain():
    global _nl_chain
    if _nl_chain is None:
        from ai.llm.chain import NLQueryChain

        _nl_chain = NLQueryChain()
    return _nl_chain


def get_langfuse():
    global _langfuse_client
    if _langfuse_client is None:
        try:
            from django.conf import settings
            from langfuse import Langfuse

            public_key = getattr(settings, 'LANGFUSE_PUBLIC_KEY', None)
            secret_key = getattr(settings, 'LANGFUSE_SECRET_KEY', None)
            if public_key and secret_key:
                _langfuse_client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=getattr(settings, 'LANGFUSE_HOST', 'https://cloud.langfuse.com'),
                )
        except Exception:
            _langfuse_client = None
    return _langfuse_client


logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: ProductSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    retrieve=extend_schema(
        responses={
            200: ProductSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Product not found'),
        },
        tags=['inventory'],
    ),
    create=extend_schema(
        request=ProductWriteSerializer,
        responses={
            201: ProductSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    update=extend_schema(
        request=ProductWriteSerializer,
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Product not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    ),
    partial_update=extend_schema(
        request=ProductWriteSerializer,
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Product not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Product not found'),
        },
        tags=['inventory'],
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    """Full CRUD for products.

    - Viewer+: list, retrieve
    - Manager+: create, update
    - Admin: delete
    """

    permission_classes = [IsAuthenticated]
    queryset = Product.objects.prefetch_related('skus').all().order_by('-created_at')
    filterset_class = ProductFilter
    search_fields = ['name', 'category__name']
    ordering_fields = ['name', 'category', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        from .repositories import InventoryRepository

        include_inactive = self.request.query_params.get('include_inactive', '').lower() == 'true'
        if include_inactive and self.request.user.role == 'admin':
            return InventoryRepository().get_all_queryset(include_inactive=True)
        return InventoryRepository().get_all_queryset(include_inactive=False)

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

    def list(self, request, *args, **kwargs):
        cache_key = f'product_list_{request.get_full_path()}'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)
        return response

    def perform_create(self, serializer):
        return InventoryService().create_product(serializer.validated_data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = self.perform_create(serializer)
        out = ProductSerializer(product, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        return InventoryService().update_product(
            serializer.instance.id,
            serializer.validated_data,
        )

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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: SKUSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    retrieve=extend_schema(
        responses={
            200: SKUSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='SKU not found'),
        },
        tags=['inventory'],
    ),
    create=extend_schema(
        request=SKUSerializer,
        responses={
            201: SKUSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    update=extend_schema(
        request=SKUSerializer,
        responses={
            200: SKUSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='SKU not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    ),
    partial_update=extend_schema(
        request=SKUSerializer,
        responses={
            200: SKUSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='SKU not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='SKU not found'),
        },
        tags=['inventory'],
    ),
)
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
            serializer.instance.id,
            serializer.validated_data,
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


@extend_schema_view(
    list=extend_schema(
        responses={
            200: StockLevelSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    retrieve=extend_schema(
        responses={
            200: StockLevelSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Stock level not found'),
        },
        tags=['inventory'],
    ),
    create=extend_schema(
        request=StockLevelSerializer,
        responses={
            201: StockLevelSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    update=extend_schema(
        request=StockLevelSerializer,
        responses={
            200: StockLevelSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Stock level not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    ),
    partial_update=extend_schema(
        request=StockLevelSerializer,
        responses={
            200: StockLevelSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Stock level not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Stock level not found'),
        },
        tags=['inventory'],
    ),
)
class StockLevelViewSet(viewsets.ModelViewSet):
    """CRUD for stock levels.

    - Viewer+: list, retrieve, low_stock
    - Manager+: update stock quantities
    """

    permission_classes = [IsAuthenticated]
    serializer_class = StockLevelSerializer
    filterset_class = StockLevelFilter
    search_fields = ['sku__code', 'sku__product__name']
    ordering_fields = ['quantity_on_hand', 'updated_at']
    ordering = ['quantity_on_hand']
    queryset = StockLevel.objects.select_related('sku__product').all().order_by('sku__code')

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'low_stock'):
            return [IsViewerOrAbove()]
        return [IsManagerOrAbove()]

    def perform_create(self, serializer):
        return InventoryService().create_stock_level(serializer.validated_data)

    def perform_update(self, serializer):
        return InventoryService().update_stock_level(
            serializer.instance.id,
            serializer.validated_data,
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

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'sku_id': {'type': 'integer'},
                            'sku_code': {'type': 'string'},
                            'product_name': {'type': 'string'},
                            'quantity_on_hand': {'type': 'integer'},
                            'reorder_point': {'type': 'integer'},
                        },
                    },
                },
                description='List of stock items below reorder point',
            ),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
        },
        tags=['inventory'],
    )
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Return items where quantity < reorder_point (cached)."""
        items = InventoryService().get_low_stock_items()
        return Response(items)

    @extend_schema(
        request=inline_serializer(
            'AdjustStockInput',
            {
                'quantity_delta': serializers.IntegerField(help_text='Positive to add stock, negative to remove'),
                'reason': serializers.CharField(required=False, allow_blank=True),
            },
        ),
        responses={
            200: StockLevelSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Stock level not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    )
    @action(detail=True, methods=['patch'], url_path='adjust-stock')
    def adjust_stock(self, request, pk=None):
        """Adjust stock quantity by a delta (positive or negative).

        Request body: {"quantity_delta": int, "reason": str (optional)}
        """
        stock = self.get_object()
        delta = request.data.get('quantity_delta')
        if delta is None:
            return Response(
                {'quantity_delta': ['This field is required.']},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        try:
            delta = int(delta)
        except (TypeError, ValueError):
            return Response(
                {'quantity_delta': ['Must be a valid integer.']},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        new_quantity = stock.quantity_on_hand + delta
        if new_quantity < 0:
            return Response(
                {
                    'status': 'error',
                    'error': 'ValidationError',
                    'message': 'Validation failed.',
                    'fields': {
                        'quantity_delta': [
                            f'Adjusting by {delta} would make quantity_on_hand ({stock.quantity_on_hand}) negative.'
                        ]
                    },
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        reason = request.data.get('reason', '')
        stock = InventoryService().adjust_stock(
            stock.id,
            delta,
            user=request.user,
            reason=reason,
        )
        out = StockLevelSerializer(stock, context={'request': request})
        return Response(out.data)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: SalesRecordSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    retrieve=extend_schema(
        responses={
            200: SalesRecordSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Sales record not found'),
        },
        tags=['inventory'],
    ),
    create=extend_schema(
        request=SalesRecordSerializer,
        responses={
            201: SalesRecordSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    update=extend_schema(
        request=SalesRecordSerializer,
        responses={
            200: SalesRecordSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Sales record not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    ),
    partial_update=extend_schema(
        request=SalesRecordSerializer,
        responses={
            200: SalesRecordSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Sales record not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Sales record not found'),
        },
        tags=['inventory'],
    ),
)
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
            serializer.instance.id,
            serializer.validated_data,
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


@extend_schema_view(
    list=extend_schema(
        responses={
            200: SupplierSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    retrieve=extend_schema(
        responses={
            200: SupplierSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Supplier not found'),
        },
        tags=['inventory'],
    ),
    create=extend_schema(
        request=SupplierSerializer,
        responses={
            201: SupplierSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    update=extend_schema(
        request=SupplierSerializer,
        responses={
            200: SupplierSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Supplier not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    ),
    partial_update=extend_schema(
        request=SupplierSerializer,
        responses={
            200: SupplierSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Supplier not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Supplier not found'),
        },
        tags=['inventory'],
    ),
)
class SupplierViewSet(viewsets.ModelViewSet):
    """Full CRUD for suppliers.

    - Viewer+: list, retrieve
    - Manager+: create, update
    - Admin: delete
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SupplierSerializer
    queryset = Supplier.objects.all().order_by('name')
    search_fields = ['name', 'contact_email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        if self.action in ('create', 'update', 'partial_update'):
            return [IsManagerOrAbove()]
        if self.action == 'destroy':
            return [IsAdminOnly()]
        return [IsManagerOrAbove()]

    def perform_create(self, serializer):
        return InventoryService().create_supplier(serializer.validated_data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier = self.perform_create(serializer)
        out = SupplierSerializer(supplier, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        return InventoryService().update_supplier(
            serializer.instance.id,
            serializer.validated_data,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        supplier = self.perform_update(serializer)
        out = SupplierSerializer(supplier, context={'request': request})
        return Response(out.data)

    def perform_destroy(self, instance):
        InventoryService().delete_supplier(instance.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: CategorySerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['inventory'],
    ),
    retrieve=extend_schema(
        responses={
            200: CategorySerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Category not found'),
        },
        tags=['inventory'],
    ),
)
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoints for categories.

    - Viewer+: list, retrieve
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    queryset = Category.objects.all().order_by('name')


class StockAdjustView(APIView):
    """Adjust stock quantity for a product.
    PATCH /api/inventory/stock/{product_id}/
    """

    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    @extend_schema(
        request=inline_serializer(
            'StockAdjustInput',
            {
                'quantity_delta': serializers.IntegerField(help_text='Positive to add stock, negative to remove'),
                'reason': serializers.CharField(required=False, allow_blank=True),
            },
        ),
        responses={
            200: StockLevelSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Stock level not found for product'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['inventory'],
    )
    def patch(self, request, product_id):
        stock = InventoryService().find_stock_for_product(product_id)
        if stock is None:
            return Response(
                {
                    'status': 'error',
                    'error': 'NotFound',
                    'message': 'Stock level not found for this product.',
                    'code': 404,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        delta = request.data.get('quantity_delta')
        if delta is None:
            return Response(
                {'quantity_delta': ['This field is required.']},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        try:
            delta = int(delta)
        except (TypeError, ValueError):
            return Response(
                {'quantity_delta': ['Must be a valid integer.']},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        new_quantity = stock.quantity_on_hand + delta
        if new_quantity < 0:
            return Response(
                {
                    'status': 'error',
                    'error': 'ValidationError',
                    'message': 'Validation failed.',
                    'fields': {
                        'quantity_delta': [
                            f'Adjusting by {delta} would make quantity_on_hand ({stock.quantity_on_hand}) negative.'
                        ]
                    },
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        reason = request.data.get('reason', '')
        stock = InventoryService().adjust_stock(stock.id, delta, user=request.user, reason=reason)
        out = StockLevelSerializer(stock, context={'request': request})
        return Response(out.data)


# --- 1. INPUT VALIDATION SERIALIZER ---
class NLQuerySerializer(serializers.Serializer):
    query = serializers.CharField(required=True)

    def validate_query(self, value):
        cleaned_value = value.strip()
        if len(cleaned_value) < 3 or len(cleaned_value) > 500:
            raise serializers.ValidationError('Query must be between 3 and 500 characters long.')
        return cleaned_value


# --- 2. CONDITIONS-TO-Q TRANSLATION ---

# Maps the NL condition operators to Django Q object field lookups.
OP_MAP = {
    'eq': '',
    'neq': '',
    'lt': '__lt',
    'lte': '__lte',
    'gt': '__gt',
    'gte': '__gte',
    'contains': '__icontains',
    'starts_with': '__istarts_with',
    'ends_with': '__iends_with',
    'in': '__in',
    'not_in': '__in',  # negated at Q construction time
}

# Field name aliases: NL field name -> actual ORM field path (for joins)
FIELD_ALIASES = {
    'product_name': 'name',
    'sku_code': 'skus__code',
    'category': 'category__name',
    'supplier_name': 'supplier__name',
    'contact_email': 'contact_email',
    'quantity_on_hand': 'skus__stock_level__quantity_on_hand',
    'quantity_available': 'skus__stock_level__quantity_on_hand',
    'reorder_point': 'skus__stock_level__reorder_point',
    'date_from': 'date',
    'date_to': 'date',
    'quantity_sold': 'quantity_sold',
    'is_active': 'is_active',
    'limit': None,  # handled separately, not a Q field
}


def _parse_condition(condition: dict) -> Q:
    field = condition.get('field')
    operator = condition.get('operator', 'eq')
    value = condition.get('value')
    alias = FIELD_ALIASES.get(field, field)
    lookup = OP_MAP.get(operator, '')
    q_key = f'{alias}{lookup}'
    if operator == 'neq':
        return ~Q(**{q_key: value})
    if operator == 'not_in' and isinstance(value, list):
        return ~Q(**{q_key: value})
    if operator == 'in' and isinstance(value, list) and not value:
        return Q(pk__in=[])  # empty → no results
    return Q(**{q_key: value})


def _build_q_from_filters(filters: NLQueryFilters) -> Q:
    conjunction = getattr(filters, 'conjunction', 'and')
    conditions = getattr(filters, 'conditions', [])
    if not conditions:
        return Q()
    q_parts = [_parse_condition(c) for c in conditions]
    if conjunction == 'or':
        return Q._new_or(q_parts[0] if len(q_parts) == 1 else q_parts)
    result = q_parts[0]
    for part in q_parts[1:]:
        result &= part
    return result


def conditions_to_q(conditions, model=Product):
    """Convert a list of Condition objects into a Django Q expression."""
    combined = Q()
    for cond in conditions:
        orm_field = FIELD_ALIASES.get(cond.field, cond.field)
        if orm_field is None:
            continue
        op_suffix = OP_MAP.get(cond.op, '')
        lookup = f'{orm_field}{op_suffix}'
        if cond.op == 'eq':
            q = Q(**{lookup: cond.value})
        elif cond.op == 'neq':
            q = ~Q(**{orm_field: cond.value})
        elif cond.op in ('in', 'not_in'):
            q = Q(**{lookup: cond.value})
            if cond.op == 'not_in':
                q = ~Q(**{lookup: cond.value})
        else:
            q = Q(**{lookup: cond.value})
        combined &= q
    return combined


def _apply_pagination(qs, page: int = 1, per_page: int = 20):
    offset = (page - 1) * per_page
    total = qs.count() if hasattr(qs, 'count') else len(qs)
    return list(qs[offset : offset + per_page]), total


# --- 3. HANDLER FUNCTIONS ---


def _handle_get_inventory(filters: NLQueryFilters) -> list:
    q = _build_q_from_filters(filters)
    results = (
        Product.objects.filter(q)
        .prefetch_related('skus__stock_level')
        .select_related('category', 'supplier')
        .values('id', 'name', 'category__name', 'supplier__name', 'skus__code', 'skus__stock_level__quantity_on_hand')[
            :50
        ]
    )
    return [
        {
            'id': r['id'],
            'name': r['name'],
            'category': r['category__name'],
            'supplier': r['supplier__name'],
            'skus': [{'code': r['skus__code'], 'stock': r['skus__stock_level__quantity_on_hand']}],
        }
        for r in results
    ]


def _handle_get_sales_report(filters: NLQueryFilters) -> list:
    q = _build_q_from_filters(filters)
    rows = (
        SalesRecord.objects.filter(q)
        .select_related('sku__product')
        .values('sku__code', 'sku__product__name', 'quantity_sold', 'date', 'unit_price')
        .order_by('-date')[:100]
    )
    return [
        {
            'sku_code': r['sku__code'],
            'product_name': r['sku__product__name'],
            'quantity_sold': r['quantity_sold'],
            'date': r['date'].isoformat() if hasattr(r['date'], 'isoformat') else str(r['date']),
            'unit_price': r['unit_price'],
        }
        for r in rows
    ]


def _handle_get_low_stock(filters: NLQueryFilters) -> list:
    q = _build_q_from_filters(filters)
    threshold = filters.get('threshold', 10)
    items = (
        StockLevel.objects.select_related('sku__product')
        .filter(q, quantity_on_hand__lt=threshold)
        .values('sku__code', 'sku__product__name', 'quantity_on_hand', 'reorder_point')
    )
    return list(items)


def _handle_forecast_demand(filters: NLQueryFilters) -> list:
    sku_code = filters.get('sku_code')
    service = ForecastingService()
    result = service.run_forecast(sku_code=sku_code)
    return result if result else []


def _handle_get_supplier_info(filters: NLQueryFilters) -> list:
    q = _build_q_from_filters(filters)
    suppliers = Supplier.objects.filter(q).values('id', 'name', 'contact_email', 'phone', 'address')
    return list(suppliers)


def _handle_get_total_value(filters: NLQueryFilters) -> list:
    q = _build_q_from_filters(filters)
    result = Product.objects.filter(q).aggregate(
        total_value=Sum(F('skus__stock_level__quantity_on_hand') * F('unit_price'), output_field=DecimalField())
    )
    return [{'total_inventory_value': float(result['total_value'] or 0.0)}]


def _handle_get_top_products(filters: NLQueryFilters) -> list:
    limit = filters.get('limit', 10)
    rows = (
        SalesRecord.objects.values('sku__code', 'sku__product__name')
        .annotate(total_sold=Sum('quantity_sold'))
        .order_by('-total_sold')[:limit]
    )
    return [
        {'sku_code': r['sku__code'], 'product_name': r['sku__product__name'], 'total_sold': r['total_sold']}
        for r in rows
    ]


_handler_map = {
    'get_inventory': _handle_get_inventory,
    'get_sales_report': _handle_get_sales_report,
    'get_low_stock': _handle_get_low_stock,
    'forecast_demand': _handle_forecast_demand,
    'get_supplier_info': _handle_get_supplier_info,
    'get_total_value': _handle_get_total_value,
    'get_top_products': _handle_get_top_products,
}


# --- 4. VIEW ---


class NLQueryEndpointView(APIView):
    permission_classes = [IsManagerOrAbove]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'nlquery'

    @extend_schema(
        request=NLQuerySerializer,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'success'},
                        'data': {
                            'type': 'object',
                            'properties': {
                                'answer': {'type': 'string', 'description': 'Natural language response'},
                                'action': {'type': 'object'},
                                'raw_data': {
                                    'type': 'array',
                                    'items': {'type': 'object'},
                                },
                            },
                        },
                    },
                },
                description='Natural language query result',
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer, description='Bad request or prompt injection detected'
            ),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
            500: OpenApiResponse(response=ErrorResponseSerializer, description='AI pipeline error'),
            504: OpenApiResponse(
                response=ErrorResponseSerializer,
                description='Gateway timeout — AI pipeline took too long',
            ),
        },
        examples=[
            OpenApiExample(
                'NL Query Request',
                value={'query': 'show me products with low stock'},
                request_only=True,
            ),
            OpenApiExample(
                'NL Query Response',
                value={
                    'status': 'success',
                    'data': {
                        'answer': 'There are 3 products with low stock: Widget A (5 units), Gadget B (3 units)',
                        'action': {'type': 'get_low_stock', 'filters': {}},
                        'raw_data': [
                            {
                                'sku_code': 'SKU001',
                                'sku__product__name': 'Widget A',
                                'quantity_on_hand': 5,
                                'reorder_point': 10,
                            }
                        ],
                    },
                },
                response_only=True,
            ),
        ],
        tags=['ai'],
    )
    def post(self, request, *args, **kwargs):
        serializer = NLQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'errors': serializer.errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        query = serializer.validated_data['query']

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_pipeline, query, request.user)
                return future.result(timeout=10)
        except TimeoutError:
            return Response(
                {'status': 'error', 'message': 'Gateway Timeout: AI pipeline took too long.'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _run_pipeline(self, query, user):
        from ai.llm.chain import call_gpt4o_formatter, prompt_injection_filter

        pipeline_start = time.time()

        # Step A: Prompt Injection Check
        is_safe = prompt_injection_filter(query)
        if not is_safe:
            AuditLog.objects.create(
                user=user,
                event='PROMPT_INJECTION_ATTEMPT',
                data_snapshot={'query': query},
            )
            return Response(
                {'status': 'error', 'message': 'Malicious query detected.'}, status=status.HTTP_400_BAD_REQUEST
            )

        # Step B: LangChain Processing
        try:
            chain_instance = get_nl_chain()
            chain_result = chain_instance.run(query)

            # Extracting information based on your structured JSON schema rules
            chain_dict = chain_result.to_dict()
            action_type = chain_dict.get('action')
            filters = chain_dict.get('filters', {})
        except Exception as chain_err:
            return Response(
                {'status': 'error', 'message': f'LLM Chain failure: {chain_err}'}, status=status.HTTP_400_BAD_REQUEST
            )

        # Step C: Dispatch to the correct service
        raw_data = None
        try:
            if action_type == 'get_inventory':
                raw_data = self._handle_get_inventory(filters)
            elif action_type == 'get_sales_report':
                raw_data = self._handle_get_sales_report(filters)
            elif action_type == 'get_low_stock':
                raw_data = self._handle_get_low_stock(filters)
            elif action_type == 'forecast_demand':
                raw_data = self._handle_forecast_demand(filters)
            elif action_type == 'get_supplier_info':
                raw_data = self._handle_get_supplier_info(filters)
            elif action_type == 'get_total_value':
                raw_data = self._handle_get_total_value(filters)
            elif action_type == 'get_top_products':
                raw_data = self._handle_get_top_products(filters)
            else:
                return Response(
                    {'status': 'error', 'message': f'Unknown action type: {action_type}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as db_err:
            logger.exception('Database execution error for action %s', action_type)
            return Response(
                {'status': 'error', 'message': f'Database execution error: {db_err}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Step D: Second LLM Call to convert data records into plain sentences
        try:
            natural_language_answer = call_gpt4o_formatter(original_query=query, raw_data=raw_data)
        except Exception as format_err:
            logger.exception('Formatter failed: %s', format_err)
            return Response(
                {'status': 'error', 'message': 'Failed to format natural language response.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Step E: Tracing
        try:
            langfuse = get_langfuse()
            if langfuse:
                langfuse.trace(
                    name='nlquery',
                    input=query,
                    output=natural_language_answer,
                    metadata={
                        'user': str(user.id),
                        'action': action_type,
                        'pipeline_time': time.time() - pipeline_start,
                    },
                )
        except Exception:
            pass

        AuditLog.objects.create(
            user=user,
            event='AI_NL_QUERY',
            data_snapshot={
                'query': query,
                'action': action_type,
                'response_length': len(natural_language_answer),
                'pipeline_time_ms': int((time.time() - pipeline_start) * 1000),
            },
        )

        return Response(
            {
                'status': 'success',
                'data': {
                    'answer': natural_language_answer,
                    'action': {'type': action_type, 'filters': filters},
                    'raw_data': raw_data,
                },
            }
        )

    def _handle_get_inventory(self, filters):
        return _handle_get_inventory(NLQueryFilters(**filters) if isinstance(filters, dict) else filters)

    def _handle_get_sales_report(self, filters):
        return _handle_get_sales_report(NLQueryFilters(**filters) if isinstance(filters, dict) else filters)

    def _handle_get_low_stock(self, filters):
        return _handle_get_low_stock(filters if isinstance(filters, dict) else filters)

    def _handle_forecast_demand(self, filters):
        return _handle_forecast_demand(filters if isinstance(filters, dict) else filters)

    def _handle_get_supplier_info(self, filters):
        return _handle_get_supplier_info(NLQueryFilters(**filters) if isinstance(filters, dict) else filters)

    def _handle_get_total_value(self, filters: NLQueryFilters):
        qs = Product.objects.filter(is_active=True).select_related('category')
        if filters.conditions:
            q = conditions_to_q(filters.conditions, model=Product)
            qs = qs.filter(q)
        total = qs.aggregate(
            total_value=Sum(
                ExpressionWrapper(
                    F('unit_price') * F('skus__stock_level__quantity_on_hand'),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
        )
        return {
            'total_value': str(total['total_value'] or 0),
            'product_count': qs.count(),
        }

    def _handle_get_top_products(self, filters: NLQueryFilters):
        from django.db.models import Sum as DjSum

        qs = SalesRecord.objects.select_related('sku__product')
        if filters.conditions:
            q = conditions_to_q(filters.conditions, model=SalesRecord)
            qs = qs.filter(q)
        top = (
            qs.values('sku__code', 'sku__product__name')
            .annotate(total_sold=DjSum('quantity_sold'))
            .order_by('-total_sold')
        )
        # Apply limit from filters
        limit = filters.limit or 10
        top = top[:limit]
        return list(top)

    # -- Tracing ---------------------------------------------------------------

    def _trace_query(self, user, query, action, filters, latency_ms):
        """Log the NL query to the audit system. Langfuse integration is optional."""
        trace_data = {
            'query': query,
            'action': action,
            'conditions': filters.to_dict(),
            'latency_ms': latency_ms,
        }

        # Audit log (always available)
        AuditLog.objects.create(
            user=user,
            event='AI_NL_QUERY',
            data_snapshot=trace_data,
        )

        # Langfuse tracing (optional — only if configured)
        try:
            lf = get_langfuse()
            if lf is not None:
                trace = lf.trace(
                    name='nl_query',
                    user_id=str(user.id) if user else 'anonymous',
                    metadata={'action': action, 'latency_ms': latency_ms},
                )
                trace.span(
                    name='query_processing',
                    input={'query': query},
                    output={'action': action, 'conditions': filters.to_dict()},
                )
                lf.flush()
        except Exception as lf_err:
            logger.debug('Langfuse trace skipped: %s', lf_err)
