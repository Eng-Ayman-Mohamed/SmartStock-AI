from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.agents.tools.confirmation_listener import ConfirmationListenerTool
from ai.agents.tools.email_send import EmailSendTool
from ai.agents.tools.po_draft import PODraftTool


class FakePurchasingServiceForTools:
    def __init__(self, po_status='approved', po_id=42):
        self.repo = MagicMock()
        self.repo.get_by_id.return_value = SimpleNamespace(
            id=po_id,
            status=po_status,
            sku=SimpleNamespace(code='SKU-001', product=SimpleNamespace(name='Widget')),
            supplier=SimpleNamespace(name='Acme Corp', contact_email='supplier@example.com'),
            quantity=100,
            total_cost='5000.00',
            requested_by=SimpleNamespace(name='John Doe'),
            supplier_id=1,
            sku_id=1,
        )
        self.repo.create.return_value = SimpleNamespace(
            id=po_id, status='draft', sku_id=1, supplier_id=1, quantity=100
        )


class PODraftToolTest(TestCase):
    def setUp(self):
        self.service = FakePurchasingServiceForTools()
        self.tool = PODraftTool(service=self.service)

    def test_creates_draft_po_with_correct_data(self):
        self.service.repo.create.return_value = SimpleNamespace(
            id=42, status='draft', sku_id=1, supplier_id=5, quantity=100
        )
        result = self.tool.run({
            'sku_id': '1',
            'quantity': '100',
            'supplier_id': '5',
            'user_id': '1',
            'agent_reasoning': 'Low stock detected',
        })

        self.assertEqual(result['po_id'], 42)
        self.assertEqual(result['status'], 'draft')
        self.assertEqual(result['sku_id'], 1)
        self.assertEqual(result['supplier_id'], 5)
        self.assertEqual(result['quantity'], 100)

    def test_creates_draft_without_user_id(self):
        result = self.tool.run({
            'sku_id': '2',
            'quantity': '50',
            'supplier_id': '3',
        })

        self.assertEqual(result['po_id'], 42)
        self.assertEqual(result['status'], 'draft')

    def test_handles_creation_failure(self):
        self.service.repo.create.side_effect = Exception('DB connection lost')
        result = self.tool.run({
            'sku_id': '1',
            'quantity': '10',
            'supplier_id': '1',
        })

        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['po_id'], None)
        self.assertIn('DB connection lost', result['error'])


class EmailSendToolTest(TestCase):
    def setUp(self):
        self.purchasing_service = FakePurchasingServiceForTools(po_status='approved')
        self.email_service = MagicMock()
        self.tool = EmailSendTool(
            purchasing_service=self.purchasing_service,
            email_service=self.email_service,
        )

    def test_sends_email_to_supplier(self):
        result = self.tool.run({
            'po_id': 42,
            'recipient_email': 'supplier@example.com',
            'supplier_name': 'Acme Corp',
        })

        self.assertEqual(result['status'], 'sent')
        self.assertEqual(result['po_id'], 42)
        self.assertIn('message_id', result)
        self.assertEqual(result['recipient'], 'supplier@example.com')
        self.email_service.send.assert_called_once()

    def test_includes_po_details_in_email(self):
        self.tool.run({
            'po_id': 42,
            'recipient_email': 'supplier@example.com',
            'supplier_name': 'Acme Corp',
        })

        call_kwargs = self.email_service.send.call_args
        subject = call_kwargs[1]['subject'] if 'subject' in call_kwargs[1] else call_kwargs[0][0]
        self.assertIn('PO-42', subject)
        self.assertIn('SKU-001', subject)

    def test_returns_failed_for_non_approved_po(self):
        self.purchasing_service = FakePurchasingServiceForTools(po_status='draft')
        tool = EmailSendTool(
            purchasing_service=self.purchasing_service,
            email_service=self.email_service,
        )
        result = tool.run({'po_id': 42})

        self.assertEqual(result['status'], 'failed')
        self.assertIn('not in approved/sent status', result['error'])

    def test_handles_email_service_exception(self):
        self.email_service.send.side_effect = Exception('SMTP timeout')
        result = self.tool.run({
            'po_id': 42,
            'recipient_email': 'supplier@example.com',
            'supplier_name': 'Acme Corp',
        })

        self.assertEqual(result['status'], 'failed')
        self.assertIn('SMTP timeout', result['error'])

    def test_generates_message_id(self):
        result = self.tool.run({
            'po_id': 42,
            'recipient_email': 'supplier@example.com',
            'supplier_name': 'Acme Corp',
        })

        self.assertIn('message_id', result)
        self.assertTrue(result['message_id'].startswith('po-42-'))


class ConfirmationListenerToolTest(TestCase):
    def setUp(self):
        self.purchasing_service = FakePurchasingServiceForTools()
        self.tool = ConfirmationListenerTool(purchasing_service=self.purchasing_service)

    def test_returns_confirmed_when_po_is_confirmed(self):
        self.purchasing_service.repo.get_by_id.return_value = SimpleNamespace(
            id=42, status='confirmed'
        )

        result = self.tool.run({'po_id': 42})

        self.assertTrue(result['confirmed'])
        self.assertEqual(result['status'], 'confirmed')

    def test_returns_not_confirmed_when_waiting(self):
        self.purchasing_service.repo.get_by_id.return_value = SimpleNamespace(
            id=42, status='waiting_confirmation'
        )

        result = self.tool.run({'po_id': 42})

        self.assertFalse(result['confirmed'])
        self.assertEqual(result['status'], 'waiting_confirmation')

    def test_returns_terminal_for_rejected_po(self):
        self.purchasing_service.repo.get_by_id.return_value = SimpleNamespace(
            id=42, status='rejected'
        )

        result = self.tool.run({'po_id': 42})

        self.assertFalse(result['confirmed'])
        self.assertTrue(result['terminal'])
        self.assertEqual(result['status'], 'rejected')

    def test_returns_terminal_for_cancelled_po(self):
        self.purchasing_service.repo.get_by_id.return_value = SimpleNamespace(
            id=42, status='cancelled'
        )

        result = self.tool.run({'po_id': 42})

        self.assertTrue(result['terminal'])

    def test_returns_terminal_for_failed_po(self):
        self.purchasing_service.repo.get_by_id.return_value = SimpleNamespace(
            id=42, status='failed'
        )

        result = self.tool.run({'po_id': 42})

        self.assertTrue(result['terminal'])

    def test_handles_exception_gracefully(self):
        self.purchasing_service.repo.get_by_id.side_effect = Exception('DB error')
        result = self.tool.run({'po_id': 42})

        self.assertFalse(result['confirmed'])
        self.assertIn('error', result)
