from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.agents.tools.confirmation_listener import ConfirmationListenerTool
from ai.agents.tools.db_update import DBUpdateTool
from ai.agents.tools.email_send import EmailSendTool
from ai.agents.tools.po_draft import PODraftTool
from core.exceptions import IllegalPOTransitionError


class PODraftToolTest(TestCase):
    def test_creates_po_and_returns_id_and_number(self):
        mock_service = MagicMock()
        mock_po = MagicMock(id=10, status='draft', sku_id=5, supplier_id=3, quantity=100)
        mock_service.repo.create.return_value = mock_po

        tool = PODraftTool(service=mock_service)
        result = tool.run({'sku_id': '5', 'quantity': '100', 'supplier_id': '3'})

        self.assertEqual(result['po_id'], 10)
        self.assertEqual(result['status'], 'draft')
        mock_service.repo.create.assert_called_once()
        call_data = mock_service.repo.create.call_args[0][0]
        self.assertEqual(call_data['sku_id'], 5)
        self.assertEqual(call_data['quantity'], 100)

    def test_computes_total_cost_from_quantity_times_unit_price(self):
        mock_service = MagicMock()
        mock_service.repo.create.return_value = MagicMock(id=1)

        tool = PODraftTool(service=mock_service)
        tool.run({'sku_id': '7', 'quantity': '25', 'supplier_id': '4', 'total_cost': '175.00'})

        call_data = mock_service.repo.create.call_args[0][0]
        self.assertEqual(call_data['total_cost'], '175.00')


class EmailSendToolTest(TestCase):
    def test_sends_email_and_returns_recipient(self):
        mock_service = MagicMock()
        mock_po = MagicMock()
        mock_po.status = 'approved'
        mock_po.sku.code = 'SKU-001'
        mock_po.sku.product.name = 'Widget'
        mock_po.quantity = 10
        mock_po.total_cost = '100.00'
        mock_po.requested_by = 'admin'
        mock_po.supplier.contact_email = 'supplier@example.com'
        mock_po.supplier.name = 'Supplier Co'
        mock_service.repo.get_by_id.return_value = mock_po

        with patch('ai.agents.tools.email_send.send_email_with_retry.delay') as mock_delay:
            mock_delay.return_value.id = 'task-123'
            tool = EmailSendTool(purchasing_service=mock_service)
            result = tool.run({'po_id': '1'})

        self.assertEqual(result['status'], 'sent')
        self.assertEqual(result['recipient'], 'supplier@example.com')

    def test_converts_po_id_string_to_int(self):
        mock_service = MagicMock()
        mock_po = MagicMock()
        mock_po.status = 'sent'
        mock_po.sku.code = 'SKU-001'
        mock_po.sku.product.name = 'Widget'
        mock_po.quantity = 10
        mock_po.total_cost = '100.00'
        mock_po.requested_by = 'admin'
        mock_po.supplier.contact_email = 'a@b.com'
        mock_po.supplier.name = 'Supplier Co'
        mock_service.repo.get_by_id.return_value = mock_po

        with patch('ai.agents.tools.email_send.send_email_with_retry.delay'):
            tool = EmailSendTool(purchasing_service=mock_service)
            tool.run({'po_id': '42'})

        mock_service.repo.get_by_id.assert_called_once_with(42)


class ConfirmationListenerToolTest(TestCase):
    def test_returns_confirmed_when_supplier_replied(self):
        mock_service = MagicMock()
        mock_po = MagicMock()
        mock_po.status = 'confirmed'
        mock_service.repo.get_by_id.return_value = mock_po

        tool = ConfirmationListenerTool(purchasing_service=mock_service)
        result = tool.run({'po_id': '1'})

        self.assertTrue(result['confirmed'])
        self.assertEqual(result['status'], 'confirmed')

    def test_returns_not_confirmed_when_no_reply(self):
        mock_service = MagicMock()
        mock_po = MagicMock()
        mock_po.status = 'draft'
        mock_service.repo.get_by_id.return_value = mock_po

        tool = ConfirmationListenerTool(purchasing_service=mock_service)
        result = tool.run({'po_id': '2'})

        self.assertFalse(result['confirmed'])

    def test_converts_po_id_string_to_int(self):
        mock_service = MagicMock()
        mock_po = MagicMock()
        mock_po.status = 'draft'
        mock_service.repo.get_by_id.return_value = mock_po

        tool = ConfirmationListenerTool(purchasing_service=mock_service)
        tool.run({'po_id': '99'})

        mock_service.repo.get_by_id.assert_called_once_with(99)


class DBUpdateToolTest(TestCase):
    def test_transitions_status_successfully(self):
        mock_service = MagicMock()
        mock_service.transition_po_status.return_value = MagicMock(id=1, status='approved')

        tool = DBUpdateTool(service=mock_service)
        result = tool.run({'po_id': '1', 'status': 'approved'})

        self.assertEqual(result['po_id'], 1)
        self.assertEqual(result['status'], 'approved')
        mock_service.transition_po_status.assert_called_once_with(1, 'approved')

    def test_raises_on_illegal_transition(self):
        mock_service = MagicMock()
        mock_service.transition_po_status.side_effect = IllegalPOTransitionError(
            'Cannot transition from "confirmed" to "draft"'
        )

        tool = DBUpdateTool(service=mock_service)
        with self.assertRaises(IllegalPOTransitionError):
            tool.run({'po_id': '1', 'status': 'draft'})

    def test_converts_po_id_string_to_int(self):
        mock_service = MagicMock()
        mock_service.transition_po_status.return_value = MagicMock(id=5, status='sent')

        tool = DBUpdateTool(service=mock_service)
        tool.run({'po_id': '5', 'status': 'sent'})

        mock_service.transition_po_status.assert_called_once_with(5, 'sent')
