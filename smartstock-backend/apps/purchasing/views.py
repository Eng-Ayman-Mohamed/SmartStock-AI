from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.permissions import IsAdminOnly, IsManagerOrAbove, IsViewerOrAbove
from apps.inventory.models import Supplier
from apps.inventory.serializers import SupplierSerializer
from config.schema_serializers import ErrorResponseSerializer, ValidationErrorResponseSerializer

from .models import PurchaseOrder
from .serializers import PurchaseOrderSerializer
from .services import PurchasingService


@extend_schema_view(
    list=extend_schema(
        responses={
            200: SupplierSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['purchasing'],
    ),
    retrieve=extend_schema(
        responses={
            200: SupplierSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Supplier not found'),
        },
        tags=['purchasing'],
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
        tags=['purchasing'],
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
        tags=['purchasing'],
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
        tags=['purchasing'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Supplier not found'),
        },
        tags=['purchasing'],
    ),
)
class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        if self.action in ('create', 'update', 'partial_update'):
            return [IsManagerOrAbove()]
        if self.action == 'destroy':
            return [IsAdminOnly()]
        return [IsManagerOrAbove()]


@extend_schema_view(
    list=extend_schema(
        responses={
            200: PurchaseOrderSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['purchasing'],
    ),
    retrieve=extend_schema(
        responses={
            200: PurchaseOrderSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Purchase order not found'),
        },
        tags=['purchasing'],
    ),
    create=extend_schema(
        request=PurchaseOrderSerializer,
        responses={
            201: PurchaseOrderSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['purchasing'],
    ),
    update=extend_schema(
        request=PurchaseOrderSerializer,
        responses={
            200: PurchaseOrderSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Purchase order not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['purchasing'],
    ),
    partial_update=extend_schema(
        request=PurchaseOrderSerializer,
        responses={
            200: PurchaseOrderSerializer,
            400: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Bad request'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Purchase order not found'),
            422: OpenApiResponse(response=ValidationErrorResponseSerializer, description='Validation error'),
        },
        tags=['purchasing'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Purchase order not found'),
        },
        tags=['purchasing'],
    ),
)
class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related(
        'sku', 'sku__product', 'supplier', 'requested_by', 'approved_by'
    ).all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        if self.action in ('approve', 'reject'):
            return [IsManagerOrAbove()]
        return [IsManagerOrAbove()]

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'approved'},
                        'po_id': {'type': 'integer'},
                    },
                },
                description='Purchase order approved',
            ),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Purchase order not found'),
        },
        tags=['purchasing'],
    )
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        po = self.get_object()
        result = PurchasingService().approve_po(po.id, request.user)
        return Response({'status': 'approved', 'po_id': result.id})

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'rejected'},
                        'po_id': {'type': 'integer'},
                    },
                },
                description='Purchase order rejected',
            ),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Purchase order not found'),
        },
        tags=['purchasing'],
    )
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        po = self.get_object()
        result = PurchasingService().reject_po(po.id, request.user)
        return Response({'status': 'rejected', 'po_id': result.id})

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'supplier_id': {'type': 'integer'},
                            'supplier_name': {'type': 'string'},
                            'overdue_pos': {'type': 'integer'},
                        },
                    },
                },
                description='List of suppliers with overdue purchase orders',
            ),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
        },
        tags=['purchasing'],
    )
    @action(detail=False, methods=['get'], url_path='overdue-suppliers')
    def overdue_suppliers(self, request):
        """Return suppliers with sent POs that exceed their lead time."""
        overdue = PurchasingService().get_overdue_suppliers()
        return Response(overdue)
