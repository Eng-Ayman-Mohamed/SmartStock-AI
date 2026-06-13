from django.core.exceptions import ValidationError
from django.dispatch import Signal
from django.utils import timezone

from apps.audit.models import AuditLog
from core.exceptions import IllegalPOTransitionError
from infrastructure.email import EmailService

from .repositories import PurchasingRepository

po_approved = Signal()
po_rejected = Signal()
po_sent = Signal()

LEGAL_TRANSITIONS = {
    'draft': ['pending_approval', 'rejected', 'cancelled'],
    'pending_approval': ['approved', 'rejected', 'cancelled'],
    'approved': ['sent', 'cancelled'],
    'sent': ['confirmed', 'cancelled'],
    'confirmed': [],
    'rejected': [],
    'cancelled': [],
}


class PurchasingService:
    def __init__(self, repo=None):
        self.repo = repo or PurchasingRepository()

    def draft_po(self, sku_id: int, quantity: int, supplier_id: int, user):
        data = {
            'sku_id': sku_id,
            'quantity': quantity,
            'supplier_id': supplier_id,
            'requested_by': user,
            'status': 'draft',
        }
        return self.repo.create(data)

    def approve_po(self, po_id: int, user):
        po = self.repo.get_by_id(po_id)
        if po.status not in ('draft', 'pending_approval'):
            raise ValidationError('Only draft or pending approval orders can be approved.')
        po = self.repo.update(po_id, {'status': 'approved', 'approved_by_id': user.id})
        po_approved.send(sender=self.__class__, po=po, user=user)
        return po

    def reject_po(self, po_id: int, user):
        po = self.repo.get_by_id(po_id)
        if po.status not in ('draft', 'pending_approval'):
            raise ValidationError('Only draft or pending approval orders can be rejected.')
        po = self.repo.update(po_id, {'status': 'rejected'})
        po_rejected.send(sender=self.__class__, po=po, user=user)
        return po

    def send_po(self, po_id: int):
        po = self.repo.get_by_id(po_id)
        if po.status != 'approved':
            raise ValidationError('Only approved orders can be sent.')
        po = self.repo.update(
            po_id,
            {
                'status': 'sent',
                'sent_at': timezone.now(),
            },
        )
        po_sent.send(sender=self.__class__, po=po)
        return po

    def get_open_po_status(self, product_id: int) -> dict:
        open_po = self.repo.get_open_for_product(product_id)
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
                        'po_number': f'PO-{po.id}',
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
                f'Cannot transition from "{current}" to "{new_status}". '
                f'Allowed: {allowed}'
            )
        update_data = {'status': new_status}
        if new_status == 'confirmed':
            update_data['confirmed_at'] = timezone.now()
        updated = self.repo.update(po_id, update_data)
        AuditLog.objects.create(
            event=f'PO_{new_status.upper()}',
            entity_type='PurchaseOrder',
            entity_id=po_id,
            data_snapshot={'from': current, 'to': new_status},
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

    def send_po_email(self, po_id: int) -> dict:
        po_data = self.get_po_with_supplier(po_id)
        from django.template.loader import render_to_string
        subject = f'Purchase Order {po_data["po_number"]} — Confirmation Required'
        message = render_to_string('purchasing/po_email.txt', po_data)
        EmailService().send(
            subject=subject,
            message=message,
            recipient=po_data['supplier_email'],
        )
        return {'sent': True, 'recipient': po_data['supplier_email']}
