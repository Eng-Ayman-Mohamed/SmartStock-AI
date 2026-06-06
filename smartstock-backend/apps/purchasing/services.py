from django.dispatch import Signal
from django.core.exceptions import ValidationError
from .repositories import PurchasingRepository

po_approved = Signal()


class PurchasingService:
    def __init__(self):
        self.repo = PurchasingRepository()

    def draft_po(self, sku_id: int, quantity: int, supplier_id: int, user):
        data = {
            "sku_id": sku_id,
            "quantity": quantity,
            "supplier_id": supplier_id,
            "requested_by": user,
            "status": "draft",
        }
        return self.repo.create(data)

    def approve_po(self, po_id: int, user):
        po = self.repo.get_by_id(po_id)
        if po.status != "draft":
            raise ValidationError("Only draft orders can be approved.")
        po = self.repo.update(po_id, {"status": "approved", "approved_by_id": user.id})
        po_approved.send(sender=self.__class__, po=po, user=user)
        return po
