import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.dispatch import Signal
from django.utils import timezone

from apps.purchasing.email_tasks import send_email_with_retry
from core.exceptions import IllegalPOTransitionError

from .models import PurchaseOrder
from .repositories import PurchasingRepository

logger = logging.getLogger(__name__)

po_approved = Signal()
po_rejected = Signal()
po_sent = Signal()
po_confirmed = Signal()
po_email_sent = Signal()
po_waiting_confirmation = Signal()
po_failed = Signal()
po_timeout = Signal()
po_transitioned = Signal()

LEGAL_TRANSITIONS = {
    'draft': ['pending_approval', 'approved', 'rejected', 'cancelled'],
    'pending_approval': ['approved', 'rejected', 'cancelled'],
    'approved': ['sent', 'email_sent', 'cancelled'],
    'email_sent': ['waiting_confirmation', 'cancelled'],
    'waiting_confirmation': ['confirmed', 'cancelled'],
    'sent': ['confirmed', 'cancelled'],
    'confirmed': [],
    'rejected': [],
    'cancelled': [],
    'failed': [],
    'timeout': [],
}


class PurchasingService:
    def __init__(self, repo=None):
        self.repo = repo or PurchasingRepository()

    @transaction.atomic
    def draft_po(
        self,
        sku_id: int,
        quantity: int,
        supplier_id: int,
        user,
        po_number: str = None,
        total_cost=None,
        agent_reasoning: str = '',
        notes: str = '',
        created_by_agent: bool = False,
        agent_name: str = '',
    ):
        active_statuses = ['draft', 'pending_approval', 'approved']
        existing = (
            PurchaseOrder.objects.select_for_update()
            .filter(
                sku_id=sku_id,
                supplier_id=supplier_id,
                quantity=quantity,
                status__in=active_statuses,
            )
            .first()
        )
        if existing:
            logger.info(
                'Dedup: returning existing PO id=%s for sku=%s supplier=%s qty=%s',
                existing.id,
                sku_id,
                supplier_id,
                quantity,
            )
            return existing

        data = {
            'sku_id': sku_id,
            'quantity': quantity,
            'supplier_id': supplier_id,
            'requested_by': user,
            'status': 'draft',
            'agent_reasoning': agent_reasoning,
            'notes': notes,
            'created_by_agent': created_by_agent,
            'agent_name': agent_name,
        }
        if po_number:
            data['po_number'] = po_number
        if total_cost is not None:
            data['total_cost'] = total_cost
        return self.repo.create(data)

    @transaction.atomic
    def approve_po(self, po_id: int, user, skip_email: bool = False):
        po = self.repo.get_by_id_for_update(po_id)
        if po.status not in ('draft', 'pending_approval'):
            raise IllegalPOTransitionError(
                f'Only draft or pending approval orders can be approved. Current status: {po.status}'
            )
        PurchaseOrder.objects.filter(pk=po_id).update(status='approved', approved_by_id=user.id)
        po.refresh_from_db()
        po_approved.send(sender=self.__class__, po=po, user=user)

        if not skip_email:
            try:
                self._dispatch_supplier_email(po)
            except Exception:
                logger.exception(
                    'Failed to dispatch supplier email for PO-%s after approval', po_id
                )

        return po

    def _dispatch_supplier_email(self, po):
        """Dispatch supplier email for an approved PO via Celery task."""
        from django.template.loader import render_to_string

        if po.message_id:
            logger.info(
                'PO-%s already has email sent (message_id=%s); skipping duplicate',
                po.id,
                po.message_id,
            )
            return

        supplier = po.supplier
        if not supplier or not getattr(supplier, 'contact_email', None):
            logger.warning('PO-%s has no supplier or contact email; skipping email dispatch', po.id)
            return

        po_data = self.get_po_with_supplier(po.id)
        subject = f'Purchase Order {po_data["po_number"]} — Confirmation Required'
        body = render_to_string('purchasing/po_email.txt', po_data)
        message_id = f'po-{po.id}-approved'

        send_email_with_retry.delay(
            subject=subject,
            body=body,
            recipient=supplier.contact_email,
            po_id=po.id,
            message_id=message_id,
        )
        logger.info(
            'PO-%s supplier email dispatched to %s (message_id=%s)',
            po.id,
            supplier.contact_email,
            message_id,
        )

    @transaction.atomic
    def reject_po(self, po_id: int, user):
        po = self.repo.get_by_id_for_update(po_id)
        if po.status not in ('draft', 'pending_approval'):
            raise IllegalPOTransitionError(
                f'Only draft or pending approval orders can be rejected. Current status: {po.status}'
            )
        PurchaseOrder.objects.filter(pk=po_id).update(status='rejected')
        po.refresh_from_db()
        po_rejected.send(sender=self.__class__, po=po, user=user)
        return po

    @transaction.atomic
    def send_po(self, po_id: int):
        po = self.repo.get_by_id_for_update(po_id)
        if po.status != 'approved':
            raise ValidationError('Only approved orders can be sent.')
        PurchaseOrder.objects.filter(pk=po_id).update(
            status='sent',
            sent_at=timezone.now(),
        )
        po.refresh_from_db()
        po_sent.send(sender=self.__class__, po=po)
        return po

    def mark_email_sent(self, po_id: int, message_id: str | None = None):
        po = self.repo.get_by_id(po_id)
        if po.status not in ('approved', 'sent'):
            raise ValidationError('Only approved or sent orders can be marked as email sent.')
        update_data: dict = {
            'status': 'email_sent',
            'sent_at': timezone.now(),
        }
        if message_id:
            update_data['message_id'] = message_id
        po = self.repo.update(po_id, update_data)
        po_email_sent.send(sender=self.__class__, po=po)
        return po

    def mark_waiting_confirmation(self, po_id: int):
        po = self.repo.get_by_id(po_id)
        if po.status != 'email_sent':
            raise ValidationError('Only email_sent orders can be moved to waiting confirmation.')
        po = self.repo.update(po_id, {'status': 'waiting_confirmation'})
        po_waiting_confirmation.send(sender=self.__class__, po=po)
        return po

    def mark_confirmed(self, po_id: int):
        po = self.repo.get_by_id(po_id)
        if po.status != 'waiting_confirmation':
            raise ValidationError('Only waiting_confirmation orders can be marked as confirmed.')
        po = self.repo.update(
            po_id,
            {
                'status': 'confirmed',
                'confirmed_at': timezone.now(),
            },
        )
        po_confirmed.send(sender=self.__class__, po=po)
        return po

    def mark_failed(self, po_id: int, error_message: str = ''):
        po = self.repo.get_by_id(po_id)
        po = self.repo.update(
            po_id,
            {
                'status': 'failed',
                'notes': error_message or po.notes,
            },
        )
        po_failed.send(sender=self.__class__, po=po)
        return po

    def mark_timeout(self, po_id: int):
        po = self.repo.get_by_id(po_id)
        po = self.repo.update(po_id, {'status': 'timeout'})
        po_timeout.send(sender=self.__class__, po=po)
        return po

    def get_open_po_status(self, product_id: int) -> dict:
        open_po = self.repo.get_open_for_product(product_id)
        return {
            'has_open_po': open_po is not None,
            'open_po_id': open_po.id if open_po else None,
        }

    def get_open_po_status_by_sku(self, sku_id: int) -> dict:
        open_po = self.repo.get_open_for_sku(sku_id)
        return {
            'has_open_po': open_po is not None,
            'open_po_id': open_po.id if open_po else None,
        }

    def get_overdue_suppliers(self):
        now = timezone.now()
        sent_pos = (
            self.repo.get_all()
            .filter(
                status='sent',
                sent_at__isnull=False,
            )
            .select_related('supplier')
        )

        overdue = {}
        for po in sent_pos:
            lead_time = po.supplier.default_lead_time_days
            deadline = po.sent_at + timezone.timedelta(days=lead_time)
            if now > deadline:
                sid = po.supplier.id
                if sid not in overdue:
                    overdue[sid] = {
                        'supplier_id': sid,
                        'supplier_name': po.supplier.name,
                        'overdue_pos': [],
                        'days_overdue': (now - deadline).days,
                    }
                overdue[sid]['overdue_pos'].append(
                    {
                        'po_id': po.id,
                        'po_number': po.po_number,
                        'sent_at': po.sent_at.isoformat(),
                        'deadline': deadline.isoformat(),
                    }
                )
        return list(overdue.values())

    def transition_po_status(self, po_id: int, new_status: str):
        po = self.repo.get_by_id(po_id)
        current = po.status
        allowed = LEGAL_TRANSITIONS.get(current, [])
        if new_status not in allowed:
            raise IllegalPOTransitionError(
                f'Cannot transition from "{current}" to "{new_status}". Allowed: {allowed}'
            )
        update_data = {'status': new_status}
        if new_status == 'confirmed':
            update_data['confirmed_at'] = timezone.now()
        updated = self.repo.update(po_id, update_data)
        po_transitioned.send(
            sender=self.__class__, po=updated, from_status=current, to_status=new_status
        )
        return updated

    def get_po_with_supplier(self, po_id: int) -> dict:
        po = self.repo.get_by_id(po_id)
        return {
            'po_id': po.id,
            'po_number': po.po_number,
            'sku_code': po.sku.code,
            'product_name': po.sku.product.name,
            'quantity': po.quantity,
            'unit_cost': str(po.sku.product.unit_price),
            'total_cost': str(po.total_cost),
            'supplier_email': po.supplier.contact_email,
            'supplier_name': po.supplier.name,
        }

    def check_confirmation(self, po_id: int) -> dict:
        po = self.repo.get_by_id(po_id)
        return {
            'confirmed': po.status == 'confirmed',
            'timed_out': False,
        }
