from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ingestion.repositories import InvoiceScanRepository
from apps.purchasing.repositories import PurchaseOrderWorkflowRepository

User = get_user_model()


class InvoiceScanRepositoryTest(TestCase):
    def setUp(self):
        self.repo = InvoiceScanRepository()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='pass1234'
        )

    def _create_scan(self):
        return self.repo.create(
            {
                'original_filename': 'inv.pdf',
                'content_type': 'application/pdf',
                'file_size': 1024,
                'uploaded_by': self.user,
            }
        )

    def test_create_and_get(self):
        scan = self._create_scan()
        self.assertIsNotNone(scan.id)
        result = self.repo.get_by_id(scan.id)
        self.assertEqual(result.original_filename, 'inv.pdf')

    def test_get_all(self):
        self._create_scan()
        all_scans = self.repo.get_all()
        self.assertGreaterEqual(all_scans.count(), 1)

    def test_update(self):
        scan = self._create_scan()
        updated = self.repo.update(scan.id, {'original_filename': 'new.pdf'})
        self.assertEqual(updated.original_filename, 'new.pdf')

    def test_delete(self):
        scan = self._create_scan()
        scan_id = scan.id
        self.repo.delete(scan_id)
        from apps.ingestion.models import InvoiceScan

        with self.assertRaises(InvoiceScan.DoesNotExist):
            self.repo.get_by_id(scan_id)

    def test_mark_confirmed(self):
        scan = self._create_scan()
        result = self.repo.mark_confirmed(scan.id, {'supplier': 'Acme'})
        from apps.ingestion.models import InvoiceScan

        self.assertEqual(result.status, InvoiceScan.Status.CONFIRMED)
        self.assertTrue(result.is_confirmed)

    def test_mark_rejected(self):
        scan = self._create_scan()
        result = self.repo.mark_rejected(scan.id)
        from apps.ingestion.models import InvoiceScan

        self.assertEqual(result.status, InvoiceScan.Status.REJECTED)


class PurchaseOrderWorkflowRepositoryTest(TestCase):
    def setUp(self):
        self.repo = PurchaseOrderWorkflowRepository()

    @patch('apps.purchasing.repositories.PurchaseOrderWorkflow')
    def test_get_by_id(self, MockWorkflow):
        self.repo.get_by_id(1)
        MockWorkflow.objects.get.assert_called_once_with(pk=1)

    @patch('apps.purchasing.repositories.PurchaseOrderWorkflow')
    def test_get_all(self, MockWorkflow):
        self.repo.get_all()
        MockWorkflow.objects.all.assert_called_once()

    @patch('apps.purchasing.repositories.PurchaseOrderWorkflow')
    def test_get_by_po_id(self, MockWorkflow):
        self.repo.get_by_po_id(42)
        MockWorkflow.objects.filter.assert_called_once_with(purchase_order_id=42)

    @patch('apps.purchasing.repositories.PurchaseOrderWorkflow')
    def test_create(self, MockWorkflow):
        self.repo.create({'status': 'active'})
        MockWorkflow.objects.create.assert_called_once_with(status='active')

    @patch('apps.purchasing.repositories.PurchaseOrderWorkflow')
    def test_update(self, MockWorkflow):
        self.repo.update(1, {'status': 'done'})
        MockWorkflow.objects.filter.assert_called_once_with(pk=1)

    @patch('apps.purchasing.repositories.PurchaseOrderWorkflow')
    def test_delete(self, MockWorkflow):
        self.repo.delete(1)
        MockWorkflow.objects.filter.assert_called_once_with(pk=1)
