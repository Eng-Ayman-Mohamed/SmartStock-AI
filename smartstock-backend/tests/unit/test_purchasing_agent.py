from types import SimpleNamespace
from unittest.mock import MagicMock

from django.test import TestCase

from ai.agents.purchasing_agent import PurchasingAgent


class FakePODraftTool:
    def __init__(self, po_id=42):
        self.po_id = po_id
        self.calls = []

    def run(self, input):
        self.calls.append(input)
        if input.get('action') == 'trace':
            return {'status': 'traced'}
        return {
            'po_id': self.po_id,
            'status': 'draft',
            'sku_id': input.get('sku_id'),
            'supplier_id': input.get('supplier_id'),
            'quantity': input.get('quantity'),
        }


class FakeEmailSendTool:
    def __init__(self, status='sent', message_id='msg-001'):
        self.status = status
        self.message_id = message_id
        self.calls = []

    def run(self, input):
        self.calls.append(input)
        if self.status == 'failed':
            return {'status': 'failed', 'error': 'SMTP connection refused'}
        return {
            'status': self.status,
            'po_id': input.get('po_id'),
            'message_id': self.message_id,
            'recipient': 'supplier@example.com',
        }


class FakeConfirmationTool:
    def __init__(self, confirm_on_attempt=2):
        self.confirm_on_attempt = confirm_on_attempt
        self.call_count = 0
        self.calls = []

    def run(self, input):
        self.call_count += 1
        self.calls.append(input)
        if self.call_count >= self.confirm_on_attempt:
            return {
                'confirmed': True,
                'po_id': input.get('po_id'),
                'status': 'confirmed',
            }
        return {
            'confirmed': False,
            'po_id': input.get('po_id'),
            'status': 'waiting_confirmation',
        }


class FakeConfirmationToolNeverConfirm:
    def __init__(self):
        self.call_count = 0

    def run(self, input):
        self.call_count += 1
        return {
            'confirmed': False,
            'po_id': input.get('po_id'),
            'status': 'waiting_confirmation',
        }


class FakePurchasingService:
    def __init__(self):
        self.approved = []
        self.rejected = []
        self.failed = []
        self.timeouted = []
        self.confirmed = []
        self.emailed = []
        self.waiting = []
        self.repo = MagicMock()

    def approve_po(self, po_id, user):
        self.approved.append(po_id)
        return SimpleNamespace(id=po_id, status='approved')

    def reject_po(self, po_id, user=None):
        self.rejected.append(po_id)
        return SimpleNamespace(id=po_id, status='rejected')

    def mark_email_sent(self, po_id, message_id=None):
        self.emailed.append((po_id, message_id))
        return SimpleNamespace(id=po_id, status='email_sent')

    def mark_waiting_confirmation(self, po_id):
        self.waiting.append(po_id)
        return SimpleNamespace(id=po_id, status='waiting_confirmation')

    def mark_confirmed(self, po_id):
        self.confirmed.append(po_id)
        return SimpleNamespace(id=po_id, status='confirmed')

    def mark_failed(self, po_id, error=''):
        self.failed.append((po_id, error))
        return SimpleNamespace(id=po_id, status='failed')

    def mark_timeout(self, po_id):
        self.timeouted.append(po_id)
        return SimpleNamespace(id=po_id, status='timeout')


class FakeWorkflowService:
    def __init__(self):
        self.workflow_counter = 0
        self.updates = []
        self.poll_increments = []

    def create_workflow(self, po_id):
        self.workflow_counter += 1
        return SimpleNamespace(
            id=self.workflow_counter,
            purchase_order_id=po_id,
            status='draft',
        )

    def get_workflow(self, po_id):
        return SimpleNamespace(id=1, purchase_order_id=po_id, status='draft')

    def update_status(self, workflow_id, status, message_id=None, error_message=None):
        self.updates.append(
            {
                'workflow_id': workflow_id,
                'status': status,
                'message_id': message_id,
                'error_message': error_message,
            }
        )
        return SimpleNamespace(id=workflow_id, status=status)

    def increment_polling_attempt(self, workflow_id):
        self.poll_increments.append(workflow_id)
        return SimpleNamespace(id=workflow_id, polling_attempts=len(self.poll_increments))

    def mark_confirmed(self, workflow_id):
        self.updates.append({'workflow_id': workflow_id, 'status': 'confirmed'})
        return SimpleNamespace(id=workflow_id, status='confirmed')


def fake_sleep(duration):
    """No-op sleep for testing."""
    pass


class PurchasingAgentApprovalAcceptedTest(TestCase):
    def setUp(self):
        self.purchasing_service = FakePurchasingService()
        self.workflow_service = FakeWorkflowService()

    def test_auto_approve_completes_full_workflow(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=10),
            email_send_tool=FakeEmailSendTool(status='sent', message_id='msg-001'),
            confirmation_tool=FakeConfirmationTool(confirm_on_attempt=1),
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=fake_sleep,
        )

        result = agent.run(
            {
                'sku_id': 1,
                'quantity': 100,
                'supplier_id': 5,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(result['po_id'], 10)
        self.assertIn(10, self.purchasing_service.approved)
        self.assertIn(10, self.purchasing_service.confirmed)

    def test_callback_approval_completes_workflow(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=20),
            email_send_tool=FakeEmailSendTool(status='sent', message_id='msg-002'),
            confirmation_tool=FakeConfirmationTool(confirm_on_attempt=1),
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=fake_sleep,
        )

        result = agent.run(
            {
                'sku_id': 2,
                'quantity': 50,
                'supplier_id': 3,
                'user': SimpleNamespace(id=1, name='Test User'),
                'approval_callback': lambda po_id: True,
            }
        )

        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(result['po_id'], 20)
        self.assertIn(20, self.purchasing_service.approved)

    def test_workflow_status_transitions_on_full_success(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=30),
            email_send_tool=FakeEmailSendTool(status='sent'),
            confirmation_tool=FakeConfirmationTool(confirm_on_attempt=1),
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=fake_sleep,
        )

        agent.run(
            {
                'sku_id': 3,
                'quantity': 200,
                'supplier_id': 2,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        statuses = [u['status'] for u in self.workflow_service.updates]
        self.assertIn('pending_approval', statuses)
        self.assertIn('approved', statuses)
        self.assertIn('email_sent', statuses)
        self.assertIn('waiting_confirmation', statuses)
        self.assertIn('confirmed', statuses)


class PurchasingAgentApprovalRejectedTest(TestCase):
    def setUp(self):
        self.purchasing_service = FakePurchasingService()
        self.workflow_service = FakeWorkflowService()

    def test_rejected_callback_returns_rejected(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=50),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationTool(),
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=fake_sleep,
        )

        result = agent.run(
            {
                'sku_id': 5,
                'quantity': 30,
                'supplier_id': 1,
                'user': SimpleNamespace(id=1, name='Test User'),
                'approval_callback': lambda po_id: False,
            }
        )

        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['po_id'], 50)
        self.assertIn(50, self.purchasing_service.rejected)

    def test_rejected_does_not_send_email(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=51),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationTool(),
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=fake_sleep,
        )

        agent.run(
            {
                'sku_id': 6,
                'quantity': 10,
                'supplier_id': 2,
                'user': SimpleNamespace(id=1, name='Test User'),
                'approval_callback': lambda po_id: False,
            }
        )

        self.assertEqual(self.purchasing_service.emailed, [])

    def test_pending_approval_without_callback(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=60),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationTool(),
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=fake_sleep,
        )

        result = agent.run(
            {
                'sku_id': 7,
                'quantity': 40,
                'supplier_id': 3,
                'user': SimpleNamespace(id=1, name='Test User'),
            }
        )

        self.assertEqual(result['status'], 'pending_approval')
        self.assertEqual(result['po_id'], 60)
        self.assertEqual(self.purchasing_service.emailed, [])


class PurchasingAgentEmailSendTest(TestCase):
    def setUp(self):
        self.purchasing_service = FakePurchasingService()
        self.workflow_service = FakeWorkflowService()

    def test_email_success_leads_to_polling(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=70),
            email_send_tool=FakeEmailSendTool(status='sent', message_id='msg-070'),
            confirmation_tool=FakeConfirmationTool(confirm_on_attempt=1),
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=fake_sleep,
        )

        result = agent.run(
            {
                'sku_id': 8,
                'quantity': 60,
                'supplier_id': 4,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        self.assertEqual(result['status'], 'confirmed')
        self.assertIn((70, 'msg-070'), self.purchasing_service.emailed)
        self.assertIn(70, self.purchasing_service.waiting)

    def test_email_failure_marks_workflow_failed(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=80),
            email_send_tool=FakeEmailSendTool(status='failed'),
            confirmation_tool=FakeConfirmationTool(),
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=fake_sleep,
        )

        result = agent.run(
            {
                'sku_id': 9,
                'quantity': 25,
                'supplier_id': 5,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['step'], 'email_send')
        self.assertIn(80, [f[0] for f in self.purchasing_service.failed])


class PurchasingAgentPollingTest(TestCase):
    def setUp(self):
        self.purchasing_service = FakePurchasingService()
        self.workflow_service = FakeWorkflowService()

    def test_polling_succeeds_after_multiple_attempts(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=90),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationTool(confirm_on_attempt=3),
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=fake_sleep,
        )

        result = agent.run(
            {
                'sku_id': 10,
                'quantity': 75,
                'supplier_id': 6,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(result['polling_attempts'], 3)

    def test_polling_timeout_after_max_attempts(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=100),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationToolNeverConfirm(),
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=fake_sleep,
            max_attempts=3,
            initial_delay=0.01,
        )

        result = agent.run(
            {
                'sku_id': 11,
                'quantity': 10,
                'supplier_id': 7,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        self.assertEqual(result['status'], 'timeout')
        self.assertEqual(result['polling_attempts'], 3)
        self.assertIn(100, self.purchasing_service.timeouted)

    def test_polling_stops_immediately_on_success(self):
        confirm_tool = FakeConfirmationTool(confirm_on_attempt=2)
        sleep_calls = []
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=110),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=confirm_tool,
            purchasing_service=self.purchasing_service,
            workflow_service=self.workflow_service,
            sleep_fn=lambda d: sleep_calls.append(d),
            max_attempts=10,
            initial_delay=1.0,
        )

        result = agent.run(
            {
                'sku_id': 12,
                'quantity': 30,
                'supplier_id': 8,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        self.assertEqual(result['status'], 'confirmed')
        self.assertEqual(len(sleep_calls), 2)
        self.assertEqual(confirm_tool.call_count, 2)


class PurchasingAgentExponentialBackoffTest(TestCase):
    def test_exponential_backoff_timing(self):
        sleep_calls = []
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=200),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationToolNeverConfirm(),
            purchasing_service=FakePurchasingService(),
            workflow_service=FakeWorkflowService(),
            sleep_fn=lambda d: sleep_calls.append(d),
            initial_delay=1.0,
            max_delay=10.0,
            max_attempts=5,
        )

        agent.run(
            {
                'sku_id': 13,
                'quantity': 5,
                'supplier_id': 9,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        self.assertEqual(sleep_calls, [1.0, 2.0, 4.0, 8.0, 10.0])

    def test_exponential_backoff_caps_at_max_delay(self):
        sleep_calls = []
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=201),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationToolNeverConfirm(),
            purchasing_service=FakePurchasingService(),
            workflow_service=FakeWorkflowService(),
            sleep_fn=lambda d: sleep_calls.append(d),
            initial_delay=1.0,
            max_delay=5.0,
            max_attempts=6,
        )

        agent.run(
            {
                'sku_id': 14,
                'quantity': 8,
                'supplier_id': 10,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        self.assertEqual(sleep_calls, [1.0, 2.0, 4.0, 5.0, 5.0, 5.0])

    def test_configurable_initial_delay(self):
        sleep_calls = []
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=202),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationToolNeverConfirm(),
            purchasing_service=FakePurchasingService(),
            workflow_service=FakeWorkflowService(),
            sleep_fn=lambda d: sleep_calls.append(d),
            initial_delay=2.0,
            max_delay=60.0,
            max_attempts=4,
        )

        agent.run(
            {
                'sku_id': 15,
                'quantity': 15,
                'supplier_id': 11,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        self.assertEqual(sleep_calls, [2.0, 4.0, 8.0, 16.0])

    def test_configurable_max_attempts(self):
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=203),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationToolNeverConfirm(),
            purchasing_service=FakePurchasingService(),
            workflow_service=FakeWorkflowService(),
            sleep_fn=fake_sleep,
            max_attempts=1,
            initial_delay=0.001,
        )

        result = agent.run(
            {
                'sku_id': 16,
                'quantity': 1,
                'supplier_id': 12,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        self.assertEqual(result['status'], 'timeout')
        self.assertEqual(result['polling_attempts'], 1)


class PurchasingAgentStatusTransitionsTest(TestCase):
    def test_full_success_transitions(self):
        wf_service = FakeWorkflowService()
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=300),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationTool(confirm_on_attempt=1),
            purchasing_service=FakePurchasingService(),
            workflow_service=wf_service,
            sleep_fn=fake_sleep,
        )

        agent.run(
            {
                'sku_id': 20,
                'quantity': 100,
                'supplier_id': 1,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        statuses = [u['status'] for u in wf_service.updates]
        expected = [
            'pending_approval',
            'approved',
            'email_sent',
            'waiting_confirmation',
            'confirmed',
        ]
        self.assertEqual(statuses, expected)

    def test_rejection_transitions(self):
        wf_service = FakeWorkflowService()
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=301),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationTool(),
            purchasing_service=FakePurchasingService(),
            workflow_service=wf_service,
            sleep_fn=fake_sleep,
        )

        agent.run(
            {
                'sku_id': 21,
                'quantity': 20,
                'supplier_id': 2,
                'user': SimpleNamespace(id=1, name='Test User'),
                'approval_callback': lambda po_id: False,
            }
        )

        statuses = [u['status'] for u in wf_service.updates]
        self.assertIn('pending_approval', statuses)
        self.assertIn('rejected', statuses)
        self.assertNotIn('email_sent', statuses)

    def test_email_failure_transitions(self):
        wf_service = FakeWorkflowService()
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=302),
            email_send_tool=FakeEmailSendTool(status='failed'),
            confirmation_tool=FakeConfirmationTool(),
            purchasing_service=FakePurchasingService(),
            workflow_service=wf_service,
            sleep_fn=fake_sleep,
        )

        agent.run(
            {
                'sku_id': 22,
                'quantity': 40,
                'supplier_id': 3,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        statuses = [u['status'] for u in wf_service.updates]
        self.assertIn('pending_approval', statuses)
        self.assertIn('approved', statuses)
        self.assertIn('failed', statuses)

    def test_timeout_transitions(self):
        wf_service = FakeWorkflowService()
        agent = PurchasingAgent(
            po_draft_tool=FakePODraftTool(po_id=303),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationToolNeverConfirm(),
            purchasing_service=FakePurchasingService(),
            workflow_service=wf_service,
            sleep_fn=fake_sleep,
            max_attempts=2,
            initial_delay=0.001,
        )

        agent.run(
            {
                'sku_id': 23,
                'quantity': 50,
                'supplier_id': 4,
                'user': SimpleNamespace(id=1, name='Test User'),
                'auto_approve': True,
            }
        )

        statuses = [u['status'] for u in wf_service.updates]
        self.assertIn('pending_approval', statuses)
        self.assertIn('approved', statuses)
        self.assertIn('email_sent', statuses)
        self.assertIn('waiting_confirmation', statuses)
        self.assertIn('timeout', statuses)


class PurchasingAgentDraftFailureTest(TestCase):
    def test_draft_failure_returns_failed(self):
        agent = PurchasingAgent(
            po_draft_tool=MagicMock(
                run=MagicMock(return_value={'status': 'failed', 'error': 'DB error'})
            ),
            email_send_tool=FakeEmailSendTool(),
            confirmation_tool=FakeConfirmationTool(),
            purchasing_service=FakePurchasingService(),
            workflow_service=FakeWorkflowService(),
            sleep_fn=fake_sleep,
        )

        result = agent.run(
            {
                'sku_id': 24,
                'quantity': 10,
                'supplier_id': 5,
                'user': SimpleNamespace(id=1, name='Test User'),
            }
        )

        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['step'], 'draft')
