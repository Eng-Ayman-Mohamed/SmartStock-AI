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
        mock_service.repo.create.return_value = MagicMock(id=10, po_number='PO-2026-001')

        with patch('ai.agents.tools.po_draft.generate_po_number', return_value='PO-2026-001'):
            tool = PODraftTool(service=mock_service)
            result = tool.run({'sku_id': '5', 'quantity': '100', 'supplier_id': '3'})

        self.assertEqual(result['po_id'], 10)
        self.assertEqual(result['po_number'], 'PO-2026-001')
        self.assertEqual(result['status'], 'draft')
        mock_service.repo.create.assert_called_once_with({
            'sku_id': 5,
            'quantity': 100,
            'supplier_id': 3,
            'status': 'draft',
            'po_number': 'PO-2026-001',
        })

    def test_converts_string_inputs_to_int(self):
        mock_service = MagicMock()
        mock_service.repo.create.return_value = MagicMock(id=1)

        with patch('ai.agents.tools.po_draft.generate_po_number', return_value='PO-2026-002'):
            tool = PODraftTool(service=mock_service)
            tool.run({'sku_id': '7', 'quantity': '25', 'supplier_id': '4'})

        call_args = mock_service.repo.create.call_args[0][0]
        self.assertIsInstance(call_args['sku_id'], int)
        self.assertIsInstance(call_args['quantity'], int)
        self.assertIsInstance(call_args['supplier_id'], int)


class EmailSendToolTest(TestCase):
    def test_sends_email_and_returns_recipient(self):
        mock_service = MagicMock()
        mock_service.send_po_email.return_value = {'sent': True, 'recipient': 'supplier@example.com'}

        tool = EmailSendTool(service=mock_service)
        result = tool.run({'po_id': '1'})

        self.assertTrue(result['sent'])
        self.assertEqual(result['recipient'], 'supplier@example.com')
        mock_service.send_po_email.assert_called_once_with(1)

    def test_converts_po_id_string_to_int(self):
        mock_service = MagicMock()
        mock_service.send_po_email.return_value = {'sent': True, 'recipient': 'a@b.com'}

        tool = EmailSendTool(service=mock_service)
        tool.run({'po_id': '42'})

        mock_service.send_po_email.assert_called_once_with(42)


class ConfirmationListenerToolTest(TestCase):
    def test_returns_confirmed_when_supplier_replied(self):
        mock_service = MagicMock()
        mock_service.check_confirmation.return_value = {'confirmed': True, 'timed_out': False}

        tool = ConfirmationListenerTool(service=mock_service)
        result = tool.run({'po_id': '1'})

        self.assertTrue(result['confirmed'])
        self.assertFalse(result['timed_out'])

    def test_returns_not_confirmed_when_no_reply(self):
        mock_service = MagicMock()
        mock_service.check_confirmation.return_value = {'confirmed': False, 'timed_out': False}

        tool = ConfirmationListenerTool(service=mock_service)
        result = tool.run({'po_id': '2'})

        self.assertFalse(result['confirmed'])

    def test_converts_po_id_string_to_int(self):
        mock_service = MagicMock()
        mock_service.check_confirmation.return_value = {'confirmed': False, 'timed_out': False}

        tool = ConfirmationListenerTool(service=mock_service)
        tool.run({'po_id': '99'})

        mock_service.check_confirmation.assert_called_once_with(99)


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
