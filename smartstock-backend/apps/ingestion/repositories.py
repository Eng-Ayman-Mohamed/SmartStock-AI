from django.utils import timezone

from core.base_repository import BaseRepository

from .models import InvoiceScan


class InvoiceScanRepository(BaseRepository):
    def get_by_id(self, id: int):
        return InvoiceScan.objects.get(pk=id)

    def get_all(self):
        return InvoiceScan.objects.all()

    def create(self, data: dict):
        return InvoiceScan.objects.create(**data)

    def update(self, id: int, data: dict):
        InvoiceScan.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: int):
        InvoiceScan.objects.filter(pk=id).delete()

    def mark_confirmed(self, scan_id: int, confirmed_data: dict):
        return self.update(
            scan_id,
            {
                'status': InvoiceScan.Status.CONFIRMED,
                'confirmed_data': confirmed_data,
                'is_confirmed': True,
                'confirmed_at': timezone.now(),
            },
        )

    def mark_rejected(self, scan_id: int):
        return self.update(
            scan_id,
            {
                'status': InvoiceScan.Status.REJECTED,
                'rejected_at': timezone.now(),
            },
        )
