from core.base_repository import BaseRepository

from .models import PurchaseOrder


class PurchasingRepository(BaseRepository):
    def get_by_id(self, id: int):
        return PurchaseOrder.objects.get(pk=id)

    def get_all(self):
        return PurchaseOrder.objects.all()

    def get_open_for_product(self, product_id: int):
        open_statuses = [
            PurchaseOrder.Status.DRAFT,
            PurchaseOrder.Status.PENDING_APPROVAL,
            PurchaseOrder.Status.APPROVED,
            PurchaseOrder.Status.SENT,
        ]
        return (
            PurchaseOrder.objects.filter(sku__product_id=product_id, status__in=open_statuses)
            .order_by('-created_at')
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
