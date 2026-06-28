from core.base_repository import BaseRepository

from .models import PurchaseOrder
from .workflow_models import PurchaseOrderWorkflow


class PurchasingRepository(BaseRepository):
    def get_by_id(self, id: int):
        return PurchaseOrder.objects.select_related(
            'sku__product', 'supplier', 'requested_by', 'approved_by'
        ).get(pk=id)

    def get_all(self):
        return PurchaseOrder.objects.select_related(
            'sku__product', 'supplier', 'requested_by', 'approved_by'
        ).all()

    def get_open_for_product(self, product_id: int):
        open_statuses = [
            PurchaseOrder.Status.DRAFT,
            PurchaseOrder.Status.PENDING_APPROVAL,
            PurchaseOrder.Status.APPROVED,
            PurchaseOrder.Status.SENT,
            PurchaseOrder.Status.EMAIL_SENT,
            PurchaseOrder.Status.WAITING_CONFIRMATION,
        ]
        return (
            PurchaseOrder.objects.filter(sku__product_id=product_id, status__in=open_statuses)
            .order_by('-created_at', '-id')
            .first()
        )

    def create(self, data: dict):
        return PurchaseOrder.objects.create(**data)

    def update(self, id: int, data: dict):
        PurchaseOrder.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        PurchaseOrder.objects.filter(pk=id).delete()

    def get_by_po_number(self, po_number: str):
        return PurchaseOrder.objects.get(po_number=po_number)

    def exists_by_po_number(self, po_number: str) -> bool:
        return PurchaseOrder.objects.filter(po_number=po_number).exists()

    def get_last_po_number(self, prefix: str) -> int | None:
        last = (
            PurchaseOrder.objects.filter(po_number__startswith=prefix)
            .order_by('-pk')
            .values_list('po_number', flat=True)
            .first()
        )
        if last:
            return int(last.split('-')[-1])
        return None

    def supplier_exists(self, supplier_id: int) -> bool:
        from apps.inventory.models import Supplier

        return Supplier.objects.filter(pk=supplier_id).exists()

    def sku_exists(self, sku_id: int) -> bool:
        from apps.inventory.models import SKU

        return SKU.objects.filter(pk=sku_id).exists()


class PurchaseOrderWorkflowRepository(BaseRepository):
    def get_by_id(self, id: int):
        return PurchaseOrderWorkflow.objects.get(pk=id)

    def get_all(self):
        return PurchaseOrderWorkflow.objects.all()

    def get_by_po_id(self, po_id: int):
        return PurchaseOrderWorkflow.objects.filter(purchase_order_id=po_id).first()

    def create(self, data: dict):
        return PurchaseOrderWorkflow.objects.create(**data)

    def update(self, id: int, data: dict):
        PurchaseOrderWorkflow.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        PurchaseOrderWorkflow.objects.filter(pk=id).delete()
