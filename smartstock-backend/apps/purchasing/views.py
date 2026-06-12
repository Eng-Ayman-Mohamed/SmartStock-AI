from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.permissions import (
    IsAdminOnly,
    IsManagerOrAbove,
    IsViewerOrAbove,
)
from apps.inventory.models import Supplier
from apps.inventory.serializers import SupplierSerializer
from config.schema_serializers import (
    ErrorResponseSerializer,
    ValidationErrorResponseSerializer,
)

from .models import PurchaseOrder
from .serializers import PurchaseOrderSerializer
from .services import PurchasingService


@extend_schema_view(
    list=extend_schema(
        responses={
            200: SupplierSerializer(many=True),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description="Authentication required"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Forbidden"
            ),
            429: OpenApiResponse(
                response=ErrorResponseSerializer, description="Too many requests"
            ),
        },
        tags=["purchasing"],
    ),
    retrieve=extend_schema(
        responses={
            200: SupplierSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description="Authentication required"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Forbidden"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description="Supplier not found"
            ),
        },
        tags=["purchasing"],
    ),
    create=extend_schema(
        request=SupplierSerializer,
        responses={
            201: SupplierSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description="Bad request"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Manager or above only"
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer,
                description="Validation error",
            ),
            429: OpenApiResponse(
                response=ErrorResponseSerializer, description="Too many requests"
            ),
        },
        tags=["purchasing"],
    ),
    update=extend_schema(
        request=SupplierSerializer,
        responses={
            200: SupplierSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description="Bad request"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Manager or above only"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description="Supplier not found"
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer,
                description="Validation error",
            ),
        },
        tags=["purchasing"],
    ),
    partial_update=extend_schema(
        request=SupplierSerializer,
        responses={
            200: SupplierSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description="Bad request"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Manager or above only"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description="Supplier not found"
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer,
                description="Validation error",
            ),
        },
        tags=["purchasing"],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Admin only"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description="Supplier not found"
            ),
        },
        tags=["purchasing"],
    ),
)
class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsViewerOrAbove()]
        if self.action in ("create", "update", "partial_update"):
            return [IsManagerOrAbove()]
        if self.action == "destroy":
            return [IsAdminOnly()]
        return [IsManagerOrAbove()]


@extend_schema_view(
    list=extend_schema(
        responses={
            200: PurchaseOrderSerializer(many=True),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description="Authentication required"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Forbidden"
            ),
            429: OpenApiResponse(
                response=ErrorResponseSerializer, description="Too many requests"
            ),
        },
        tags=["purchasing"],
    ),
    retrieve=extend_schema(
        responses={
            200: PurchaseOrderSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description="Authentication required"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Forbidden"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description="Purchase order not found"
            ),
        },
        tags=["purchasing"],
    ),
    create=extend_schema(
        request=PurchaseOrderSerializer,
        responses={
            201: PurchaseOrderSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description="Bad request"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Manager or above only"
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer,
                description="Validation error",
            ),
            429: OpenApiResponse(
                response=ErrorResponseSerializer, description="Too many requests"
            ),
        },
        tags=["purchasing"],
    ),
    update=extend_schema(
        request=PurchaseOrderSerializer,
        responses={
            200: PurchaseOrderSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description="Bad request"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Manager or above only"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description="Purchase order not found"
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer,
                description="Validation error",
            ),
        },
        tags=["purchasing"],
    ),
    partial_update=extend_schema(
        request=PurchaseOrderSerializer,
        responses={
            200: PurchaseOrderSerializer,
            400: OpenApiResponse(
                response=ValidationErrorResponseSerializer, description="Bad request"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Manager or above only"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description="Purchase order not found"
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer,
                description="Validation error",
            ),
        },
        tags=["purchasing"],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Admin only"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description="Purchase order not found"
            ),
        },
        tags=["purchasing"],
    ),
)
class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related(
        "sku", "sku__product", "supplier", "requested_by", "approved_by"
    ).all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsViewerOrAbove()]
        if self.action in ("approve", "reject"):
            return [IsManagerOrAbove()]
        return [IsManagerOrAbove()]

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "approved"},
                        "po_id": {"type": "integer"},
                    },
                },
                description="Purchase order approved",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description="Authentication required"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Manager or above only"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description="Purchase order not found"
            ),
        },
        tags=["purchasing"],
    )
    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        po = self.get_object()
        result = PurchasingService().approve_po(po.id, request.user)
        return Response({"status": "approved", "po_id": result.id})

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "rejected"},
                        "po_id": {"type": "integer"},
                    },
                },
                description="Purchase order rejected",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description="Authentication required"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Manager or above only"
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description="Purchase order not found"
            ),
        },
        tags=["purchasing"],
    )
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        po = self.get_object()
        result = PurchasingService().reject_po(po.id, request.user)
        return Response({"status": "rejected", "po_id": result.id})

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "supplier_id": {"type": "integer"},
                            "supplier_name": {"type": "string"},
                            "overdue_pos": {"type": "integer"},
                        },
                    },
                },
                description="List of suppliers with overdue purchase orders",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description="Authentication required"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Manager or above only"
            ),
        },
        tags=["purchasing"],
    )
    @action(detail=False, methods=["get"], url_path="overdue-suppliers")
    def overdue_suppliers(self, request):
        """Return suppliers with sent POs that exceed their lead time."""
        overdue = PurchasingService().get_overdue_suppliers()
        return Response(overdue)

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "sku_id": {"type": "integer", "description": "SKU ID to purchase"},
                    "quantity": {"type": "integer", "description": "Quantity needed"},
                    "supplier_id": {"type": "integer", "description": "Supplier ID"},
                    "agent_reasoning": {
                        "type": "string",
                        "description": "Why this order is needed",
                    },
                    "auto_approve": {
                        "type": "boolean",
                        "description": "Skip human approval gate",
                        "default": False,
                    },
                },
                "required": ["sku_id", "quantity", "supplier_id"],
            },
        },
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string"},
                        "status": {"type": "string"},
                        "po_id": {"type": "integer"},
                    },
                },
                description="Workflow result",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description="Authentication required"
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description="Manager or above only"
            ),
            422: OpenApiResponse(
                response=ValidationErrorResponseSerializer,
                description="Validation error",
            ),
        },
        tags=["purchasing"],
    )
    @action(detail=False, methods=["post"], url_path="agent-workflow")
    def agent_workflow(self, request):
        """Trigger the purchasing agent workflow with HITL approval gate."""
        from ai.agents.purchasing_agent import PurchasingAgent

        sku_id = request.data.get("sku_id")
        quantity = request.data.get("quantity")
        supplier_id = request.data.get("supplier_id")

        if not all([sku_id, quantity, supplier_id]):
            return Response(
                {
                    "status": "error",
                    "message": "sku_id, quantity, and supplier_id are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        context = {
            "sku_id": int(sku_id),
            "quantity": int(quantity),
            "supplier_id": int(supplier_id),
            "user": request.user,
            "agent_reasoning": request.data.get("agent_reasoning", ""),
            "auto_approve": request.data.get("auto_approve", False),
        }

        agent = PurchasingAgent()
        result = agent.run(context)
        result_status = result.get("status")
        http_status_map = {
            "failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "pending_approval": status.HTTP_202_ACCEPTED,
            "rejected": status.HTTP_409_CONFLICT,
            "timeout": status.HTTP_408_REQUEST_TIMEOUT,
        }
        http_status = http_status_map.get(result_status, status.HTTP_200_OK)
        return Response(result, status=http_status)
