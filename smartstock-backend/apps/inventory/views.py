from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer

from apps.authentication.permissions import IsViewerOrAbove, IsManagerOrAbove, IsAdminOnly
from .filters import ProductFilter, SKUFilter, StockLevelFilter, SalesRecordFilter
from .serializers import (
    ProductSerializer,
    ProductWriteSerializer,
    SKUSerializer,
    StockLevelSerializer,
    SalesRecordSerializer,
    SupplierSerializer,
    CategorySerializer,
)
from .services import InventoryService, SKUService, SalesRecordService
from .models import Product, SKU, StockLevel, SalesRecord, Supplier, Category

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from rest_framework.views import APIView
from rest_framework import serializers
from apps.forecasting.services import ForecastingService
from apps.audit.models import AuditLog
from apps.inventory.models import Supplier
from ai.llm.chain import NLQueryChain, prompt_injection_filter, call_gpt4o_formatter
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
        cache_key = f"product_list_{request.get_full_path()}"
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
            serializer.instance.id, serializer.validated_data,
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
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            delta = int(delta)
        except (TypeError, ValueError):
            return Response(
                {'quantity_delta': ['Must be a valid integer.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reason = request.data.get('reason', '')
        stock = InventoryService().adjust_stock(
            stock.id, delta, user=request.user, reason=reason,
        )
        out = StockLevelSerializer(stock, context={'request': request})
        return Response(out.data)


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
            serializer.instance.id, serializer.validated_data,
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
        request=inline_serializer('StockAdjustInput', {
            'quantity_delta': serializers.IntegerField(),
            'reason': serializers.CharField(required=False, allow_blank=True),
        }),
        responses={200: StockLevelSerializer, 404: None, 422: None},
    )
    def patch(self, request, product_id):
        stock = InventoryService().find_stock_for_product(product_id)
        if stock is None:
            return Response(
                {'status': 'error', 'error': 'NotFound', 'message': 'Stock level not found for this product.', 'code': 404},
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
            raise serializers.ValidationError(
                "Query must be between 3 and 500 characters long."
            )
        return cleaned_value


# --- 2. ORCHESTRATOR VIEW ENDPOINT ---
class NLQueryEndpointView(APIView):
    permission_classes = [IsManagerOrAbove]

    @extend_schema(
        request=NLQuerySerializer,
        responses={200: None, 422: NLQuerySerializer, 504: None},
    )
    def post(self, request, *args, **kwargs):
        serializer = NLQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        query = serializer.validated_data['query']

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._run_pipeline, query, request.user)
                return future.result(timeout=10)
        except TimeoutError:
            return Response(
                {"status": "error", "message": "Gateway Timeout: AI pipeline took too long."},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _run_pipeline(self, query, user):
        # Step A: Prompt Injection Check
        is_safe = prompt_injection_filter(query)
        if not is_safe:
            AuditLog.objects.create(
                user=user,
                event="PROMPT_INJECTION_ATTEMPT",
                data_snapshot={"query": query},
            )
            return Response(
                {"status": "error", "message": "Malicious query detected."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step B: LangChain Processing
        try:
            chain_instance = NLQueryChain()
            chain_result = chain_instance.run(query)
            
            # Extracting information based on your structured JSON schema rules
            chain_dict = chain_result.to_dict()
            action_type = chain_dict.get("action")
            filters = chain_dict.get("filters", {})
        except Exception as chain_err:
            return Response(
                {"status": "error", "message": f"LLM Chain failure: {str(chain_err)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step C: Dispatch to the correct service
        raw_data = None
        try:
            if action_type == "get_inventory":
                raw_data = list(InventoryService().get_all_products().values(
                    "id", "name", "category", "description"
                ))
            elif action_type == "get_sales_report":
                from .services import SalesRecordService
                records = SalesRecordService().get_all_sales_records().values(
                    "sku__code", "date", "quantity_sold"
                )
                raw_data = list(records)
            elif action_type == "get_low_stock":
                raw_data = InventoryService().get_low_stock_items()
            elif action_type == "forecast_demand":
                raw_data = ForecastingService().get_forecast(filters)
            elif action_type == "get_supplier_info":
                suppliers = Supplier.objects.values(
                    "id", "name", "contact_email", "contact_phone",
                    "default_lead_time_days", "is_active"
                )
                raw_data = list(suppliers)
            else:
                return Response(
                    {"status": "error", "message": f"Unknown action type: {action_type}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as db_err:
            return Response(
                {"status": "error", "message": f"Database execution error: {str(db_err)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step D: Second LLM Call to convert data records into plain sentences
        try:
            natural_language_answer = call_gpt4o_formatter(original_query=query, raw_data=raw_data)
        except Exception as format_err:
            return Response(
                {"status": "error", "message": "Failed to format natural language response."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step E: Return structured backend JSON payload
        return Response({
            "status": "success",
            "data": {
                "answer": natural_language_answer,
                "action": chain_result,
                "raw_data": raw_data
            }
        }, status=status.HTTP_200_OK)