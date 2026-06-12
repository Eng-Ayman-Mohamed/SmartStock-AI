from django.core.exceptions import ValidationError
from django.dispatch import Signal
from django.utils import timezone

from .repositories import PurchasingRepository

po_approved = Signal()
po_rejected = Signal()
po_sent = Signal()
po_confirmed = Signal()


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
        po_sent.send(sender=self.__class__, po=po)
        return po

    def mark_waiting_confirmation(self, po_id: int):
        po = self.repo.get_by_id(po_id)
        if po.status != 'email_sent':
            raise ValidationError('Only email_sent orders can be moved to waiting confirmation.')
        po = self.repo.update(po_id, {'status': 'waiting_confirmation'})
        return po

    def mark_confirmed(self, po_id: int):
        po = self.repo.get_by_id(po_id)
        if po.status != 'waiting_confirmation':
            raise ValidationError(
                'Only waiting_confirmation orders can be marked as confirmed.'
            )
        po = self.repo.update(po_id, {
            'status': 'confirmed',
            'confirmed_at': timezone.now(),
        })
        po_confirmed.send(sender=self.__class__, po=po)
        return po

    def mark_failed(self, po_id: int, error_message: str = ''):
        po = self.repo.get_by_id(po_id)
        po = self.repo.update(po_id, {
            'status': 'failed',
            'notes': error_message or po.notes,
        })
        return po

    def mark_timeout(self, po_id: int):
        po = self.repo.get_by_id(po_id)
        po = self.repo.update(po_id, {'status': 'timeout'})
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
