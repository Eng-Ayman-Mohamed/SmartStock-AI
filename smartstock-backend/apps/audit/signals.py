from django.dispatch import receiver
from apps.purchasing.services import po_approved
from apps.inventory.services import stock_adjusted
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


@receiver(stock_adjusted)
def log_stock_adjustment(sender, stock_level, delta, user, reason, **kwargs):
    AuditLog.objects.create(
        event="STOCK_ADJUSTED",
        user=user,
        entity_id=stock_level.id,
        data={
            "sku_code": stock_level.sku.code,
            "delta": delta,
            "new_quantity": stock_level.quantity_on_hand,
            "reason": reason,
        },
    )
