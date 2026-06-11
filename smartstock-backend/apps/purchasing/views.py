from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.authentication.permissions import IsAdminOnly, IsManagerOrAbove, IsViewerOrAbove
from apps.inventory.models import Supplier

from .models import PurchaseOrder
from .serializers import PurchaseOrderSerializer, SupplierSerializer
from .services import PurchasingService


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

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        po = self.get_object()
        result = PurchasingService().approve_po(po.id, request.user)
        return Response({'status': 'approved', 'po_id': result.id})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        po = self.get_object()
        result = PurchasingService().reject_po(po.id, request.user)
        return Response({'status': 'rejected', 'po_id': result.id})

    @action(detail=False, methods=['get'], url_path='overdue-suppliers')
    def overdue_suppliers(self, request):
        """Return suppliers with sent POs that exceed their lead time."""
        overdue = PurchasingService().get_overdue_suppliers()
        return Response(overdue)
