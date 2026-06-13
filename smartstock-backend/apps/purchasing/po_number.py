from django.utils import timezone

from .models import PurchaseOrder


def generate_po_number() -> str:
    year = timezone.now().year
    prefix = f'PO-{year}-'
    last = PurchaseOrder.objects.filter(po_number__startswith=prefix).order_by('-po_number').first()
    if last:
        last_seq = int(last.po_number.split('-')[-1])
        next_seq = last_seq + 1
    else:
        next_seq = 1
    return f'{prefix}{next_seq:03d}'
