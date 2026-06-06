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

import asyncio
from concurrent.futures import TimeoutError
from rest_framework.views import APIView
from rest_framework import serializers
from apps.forecasting.services import ForecastingService
from apps.audit.models import AuditLog                 
from ai.llm.chain import LLMChain, prompt_injection_filter, call_gpt4o_formatter
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
        return InventoryService().get_all_products()

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
    # Using your existing IsManagerOrAbove permission imported at the top of your file!
    permission_classes = [IsManagerOrAbove]

    def post(self, request, *args, **kwargs):
        # Validate incoming body data
        serializer = NLQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "errors": serializer.errors},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        query = serializer.validated_data['query']

        try:
            # Enforce 10-second absolute execution timeout limit using asyncio
            return asyncio.run(self.orchestrate_pipeline(query, request.user))
            
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

    async def orchestrate_pipeline(self, query, user):
        return await asyncio.wait_for(self._run_pipeline(query, user), timeout=10.0)

    async def _run_pipeline(self, query, user):
        # Step A: Prompt Injection Check
        is_safe = prompt_injection_filter(query)
        if not is_safe:
            # Create entry directly in your audit log app
            AuditLog.objects.create(
                user=user, 
                action="PROMPT_INJECTION_ATTEMPT", 
                details=f"Blocked query: {query}"
            )
            return Response(
                {"status": "error", "message": "Malicious query detected."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step B: LangChain Processing
        try:
            chain_instance = LLMChain()
            chain_result = chain_instance.run(query)
            
            # Extracting information based on your structured JSON schema rules
            action_type = chain_result.get("action")
            filters = chain_result.get("filters", {})
        except Exception as chain_err:
            return Response(
                {"status": "error", "message": f"LLM Chain failure: {str(chain_err)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step C: Dispatch requests dynamically using your clean service architecture
        raw_data = None
        try:
            # Instantiating services matching the design used in your ViewSets
            if action_type == "get_inventory":
                raw_data = InventoryService().get_all_products()  # Maps to your method
            elif action_type == "get_sales_report":
                raw_data = InventoryService().get_all_stock_levels() # Fallback or update to match your SalesService
            elif action_type == "get_low_stock":
                raw_data = InventoryService().get_low_stock_items() # Maps directly to your low_stock action
            elif action_type == "forecast_demand":
                raw_data = ForecastingService().get_forecast(filters)
            elif action_type == "get_supplier_info":
                # Maps to your inventory/purchasing service lookup method
                raw_data = InventoryService().get_all_products()  
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