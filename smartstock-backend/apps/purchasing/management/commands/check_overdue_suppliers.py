from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Check for overdue suppliers and create notification records'

    def handle(self, *args, **options):
        from apps.notifications.models import Notification
        from apps.notifications.service import NotificationService
        from apps.purchasing.services import PurchasingService

        overdue = PurchasingService().get_overdue_suppliers()
        self.stdout.write(f'Found {len(overdue)} overdue suppliers')

        created = 0
        for supplier in overdue:
            existing = Notification.objects.filter(
                type='escalation',
                title__startswith=f'Supplier non-response: {supplier["supplier_name"]}',
            ).exists()
            if existing:
                self.stdout.write(f'  SKIP (exists): {supplier["supplier_name"]}')
                continue

            po_numbers = ', '.join(po['po_number'] for po in supplier['overdue_pos'])
            NotificationService.create(
                type='escalation',
                severity='warning',
                title=f'Supplier non-response: {supplier["supplier_name"]}',
                message=(
                    f'{supplier["supplier_name"]} has not responded within the expected timeframe. '
                    f'Overdue by {supplier["days_overdue"]} day(s). '
                    f'POs: {po_numbers}'
                ),
                metadata={
                    'supplier_id': supplier['supplier_id'],
                    'supplier_name': supplier['supplier_name'],
                    'days_overdue': supplier['days_overdue'],
                    'overdue_pos': supplier['overdue_pos'],
                    'source': 'overdue_supplier_check',
                },
            )
            created += 1
            self.stdout.write(
                f'  CREATED: {supplier["supplier_name"]} ({supplier["days_overdue"]} days overdue)'
            )

        self.stdout.write(self.style.SUCCESS(f'Done. Created {created} notifications.'))
