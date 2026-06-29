import logging

from django.dispatch import receiver

from apps.inventory.services import stock_adjusted
from apps.purchasing.services import (
    po_approved,
    po_confirmed,
    po_email_sent,
    po_failed,
    po_rejected,
    po_sent,
    po_timeout,
    po_transitioned,
    po_waiting_confirmation,
)

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
            entity_type='PurchaseOrder',
            entity_id=po.id,
            data_snapshot={
                'supplier': po.supplier.name,
                'amount': str(po.total_cost),
                'sku': po.sku.code,
            },
        )
    except Exception as e:
        logger.exception('Failed to log PO approval audit entry: %s', e)


@receiver(po_rejected)
def log_po_rejection(sender, po, user, **kwargs):
    try:
        AuditLog.objects.create(
            event='PO_REJECTED',
            user=user,
            entity_type='PurchaseOrder',
            entity_id=po.id,
            data_snapshot={
                'supplier': po.supplier.name,
                'amount': str(po.total_cost),
                'sku': po.sku.code,
            },
        )
    except Exception as e:
        logger.exception('Failed to log PO rejection audit entry: %s', e)


@receiver(po_sent)
def log_po_sent(sender, po, **kwargs):
    try:
        AuditLog.objects.create(
            event='PO_SENT',
            entity_type='PurchaseOrder',
            entity_id=po.id,
            data_snapshot={
                'supplier': po.supplier.name,
                'sku': po.sku.code,
                'amount': str(po.total_cost),
            },
        )
    except Exception as e:
        logger.exception('Failed to log PO sent audit entry: %s', e)


@receiver(po_confirmed)
def log_po_confirmed(sender, po, **kwargs):
    try:
        AuditLog.objects.create(
            event='INVOICE_CONFIRMED',
            entity_type='PurchaseOrder',
            entity_id=po.id,
            data_snapshot={
                'supplier': po.supplier.name,
                'sku': po.sku.code,
                'amount': str(po.total_cost),
            },
        )
    except Exception as e:
        logger.exception('Failed to log PO confirmed audit entry: %s', e)


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


@receiver(po_email_sent)
def log_po_email_sent(sender, po, **kwargs):
    try:
        AuditLog.objects.create(
            event='PO_EMAIL_SENT',
            entity_type='PurchaseOrder',
            entity_id=po.id,
            data_snapshot={
                'supplier': po.supplier.name,
                'sku': po.sku.code,
                'amount': str(po.total_cost),
            },
        )
    except Exception as e:
        logger.exception('Failed to log PO email sent audit entry: %s', e)


@receiver(po_waiting_confirmation)
def log_po_waiting_confirmation(sender, po, **kwargs):
    try:
        AuditLog.objects.create(
            event='PO_WAITING_CONFIRMATION',
            entity_type='PurchaseOrder',
            entity_id=po.id,
            data_snapshot={
                'supplier': po.supplier.name,
                'sku': po.sku.code,
            },
        )
    except Exception as e:
        logger.exception('Failed to log PO waiting confirmation audit entry: %s', e)


@receiver(po_failed)
def log_po_failed(sender, po, **kwargs):
    try:
        AuditLog.objects.create(
            event='PO_FAILED',
            entity_type='PurchaseOrder',
            entity_id=po.id,
            data_snapshot={
                'supplier': po.supplier.name,
                'sku': po.sku.code,
            },
        )
    except Exception as e:
        logger.exception('Failed to log PO failed audit entry: %s', e)


@receiver(po_timeout)
def log_po_timeout(sender, po, **kwargs):
    try:
        AuditLog.objects.create(
            event='PO_TIMEOUT',
            entity_type='PurchaseOrder',
            entity_id=po.id,
            data_snapshot={
                'supplier': po.supplier.name,
                'sku': po.sku.code,
            },
        )
    except Exception as e:
        logger.exception('Failed to log PO timeout audit entry: %s', e)


@receiver(po_transitioned)
def log_po_transitioned(sender, po, from_status, to_status, **kwargs):
    """Audit log for generic PO status transitions (e.g. AI agent driven)."""
    try:
        AuditLog.objects.create(
            event=f'PO_{to_status.upper()}',
            entity_type='PurchaseOrder',
            entity_id=po.id,
            data_snapshot={
                'from': from_status,
                'to': to_status,
                'supplier': po.supplier.name if po.supplier else '',
            },
        )
    except Exception as e:
        logger.exception('Failed to log PO transition audit entry: %s', e)


def log_event(event, user, entity_type=None, entity_id=None, data_snapshot=None):
    """Utility function to create audit log entries from any signal or view."""
    try:
        AuditLog.objects.create(
            event=event,
            user=user,
            entity_type=entity_type or '',
            entity_id=entity_id,
            data_snapshot=data_snapshot or {},
        )
    except Exception as e:
        logger.exception('Failed to log audit event %s: %s', event, e)
