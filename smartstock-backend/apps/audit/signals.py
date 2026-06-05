from django.dispatch import receiver
from apps.purchasing.services import po_approved
from .models import AuditLog


@receiver(po_approved)
def log_po_approval(sender, po, user, **kwargs):
    AuditLog.objects.create(
        event="PO_APPROVED",
        user=user,
        entity_id=po.id,
        data={
            "supplier": po.supplier.name,
            "amount": str(po.total_cost),
        },
    )
