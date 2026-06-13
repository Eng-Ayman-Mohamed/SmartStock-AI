import logging

from django.dispatch import receiver

from apps.inventory.services import stock_adjusted
from apps.purchasing.services import po_approved

from .models import AuditLog

logger = logging.getLogger(__name__)


@receiver(po_approved)
def log_po_approval(sender, po, user, **kwargs):
    from apps.authentication.models import CustomUser

    if not isinstance(user, CustomUser):
        return
    try:
        AuditLog.objects.create(
            event='PO_APPROVED',
            user=user,
            entity_id=po.id,
            data_snapshot={
                'supplier': po.supplier.name,
                'amount': str(po.total_cost),
            },
        )
    except Exception as e:
        logger.exception('Failed to log PO approval audit entry: %s', e)


@receiver(stock_adjusted)
def log_stock_adjustment(sender, stock_level, delta, user, reason, **kwargs):
    from apps.authentication.models import CustomUser

    if not isinstance(user, CustomUser):
        return
    try:
        AuditLog.objects.create(
            event='STOCK_ADJUSTED',
            user=user,
            entity_id=stock_level.id,
            data_snapshot={
                'sku_code': stock_level.sku.code,
                'delta': delta,
                'new_quantity': stock_level.quantity_on_hand,
                'reason': reason,
            },
        )
    except Exception as e:
        logger.exception('Failed to log stock adjustment audit entry: %s', e)


def log_event(event, user, entity_id=None, data_snapshot=None):
    """Utility function to create audit log entries from any signal or view."""
    try:
        AuditLog.objects.create(
            event=event,
            user=user,
            entity_id=entity_id,
            data_snapshot=data_snapshot or {},
        )
    except Exception as e:
        logger.exception('Failed to log audit event %s: %s', event, e)
