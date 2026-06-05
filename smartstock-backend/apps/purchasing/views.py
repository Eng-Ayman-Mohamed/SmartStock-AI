from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PurchaseOrder, Supplier
from .serializers import PurchaseOrderSerializer, SupplierSerializer
from .services import PurchasingService


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('sku', 'supplier', 'requested_by').all()
    serializer_class = PurchaseOrderSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        po = self.get_object()
        result = PurchasingService().approve_po(po.id, request.user)
        return Response({"status": "approved", "po_id": result.id})
