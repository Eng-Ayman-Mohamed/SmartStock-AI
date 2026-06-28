def generate_po_number(last_seq: int | None = None) -> str:
    from django.utils import timezone

    year = timezone.now().year
    next_seq = (last_seq + 1) if last_seq else 1
    return f'PO-{year}-{next_seq:03d}'
