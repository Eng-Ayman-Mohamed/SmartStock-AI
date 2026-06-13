from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.purchasing.po_number import generate_po_number


class GeneratePoNumberTest(TestCase):
    @patch('apps.purchasing.po_number.PurchaseOrder')
    def test_first_po_of_year_returns_PO_YYYY_001(self, mock_po):
        mock_po.objects.filter.return_value.order_by.return_value.first.return_value = None
        result = generate_po_number()
        self.assertEqual(result, 'PO-2026-001')

    @patch('apps.purchasing.po_number.PurchaseOrder')
    def test_sequential_number_increments(self, mock_po):
        mock_po.objects.filter.return_value.order_by.return_value.first.return_value = MagicMock(
            po_number='PO-2026-005'
        )
        result = generate_po_number()
        self.assertEqual(result, 'PO-2026-006')

    @patch('apps.purchasing.po_number.PurchaseOrder')
    @patch('apps.purchasing.po_number.timezone')
    def test_resets_yearly(self, mock_tz, mock_po):
        mock_tz.now.return_value.year = 2027
        mock_po.objects.filter.return_value.order_by.return_value.first.return_value = None
        result = generate_po_number()
        self.assertEqual(result, 'PO-2027-001')
