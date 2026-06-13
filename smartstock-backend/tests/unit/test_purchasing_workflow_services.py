from types import SimpleNamespace

from django.test import TestCase

from apps.purchasing.workflow_models import PurchaseOrderWorkflow
from apps.purchasing.workflow_services import PurchaseOrderWorkflowService


class FakeWorkflowRepository:
    def __init__(self):
        self.store = {}
        self.counter = 0

    def get_by_id(self, id):
        return self.store.get(id)

    def get_by_po_id(self, po_id):
        for wf in self.store.values():
            if wf.purchase_order_id == po_id:
                return wf
        return None

    def create(self, data):
        self.counter += 1
        wf = SimpleNamespace(
            id=self.counter,
            polling_attempts=0,
            last_poll_at=None,
            message_id=None,
            error_message='',
        )
        for k, v in data.items():
            setattr(wf, k, v)
        self.store[self.counter] = wf
        return wf

    def update(self, id, data):
        wf = self.store.get(id)
        if wf:
            for k, v in data.items():
                setattr(wf, k, v)
        return wf

    def get_all(self):
        return list(self.store.values())


class PurchaseOrderWorkflowServiceTest(TestCase):
    def setUp(self):
        self.repo = FakeWorkflowRepository()
        self.service = PurchaseOrderWorkflowService(repo=self.repo)

    def test_create_workflow(self):
        workflow = self.service.create_workflow(po_id=42)

        self.assertEqual(workflow.purchase_order_id, 42)
        self.assertEqual(workflow.status, 'draft')

    def test_get_workflow_by_po_id(self):
        self.service.create_workflow(po_id=42)
        workflow = self.service.get_workflow(po_id=42)

        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.purchase_order_id, 42)

    def test_get_workflow_by_id(self):
        workflow = self.service.create_workflow(po_id=42)
        retrieved = self.service.get_workflow_by_id(workflow.id)

        self.assertEqual(retrieved.id, workflow.id)

    def test_update_status(self):
        workflow = self.service.create_workflow(po_id=42)
        updated = self.service.update_status(
            workflow.id, PurchaseOrderWorkflow.Status.PENDING_APPROVAL
        )

        self.assertEqual(updated.status, 'pending_approval')

    def test_update_status_with_message_id(self):
        workflow = self.service.create_workflow(po_id=42)
        updated = self.service.update_status(
            workflow.id,
            PurchaseOrderWorkflow.Status.EMAIL_SENT,
            message_id='msg-001',
        )

        self.assertEqual(updated.status, 'email_sent')
        self.assertEqual(updated.message_id, 'msg-001')

    def test_update_status_with_error_message(self):
        workflow = self.service.create_workflow(po_id=42)
        updated = self.service.update_status(
            workflow.id,
            PurchaseOrderWorkflow.Status.FAILED,
            error_message='SMTP connection refused',
        )

        self.assertEqual(updated.status, 'failed')
        self.assertEqual(updated.error_message, 'SMTP connection refused')

    def test_increment_polling_attempt(self):
        workflow = self.service.create_workflow(po_id=42)
        updated = self.service.increment_polling_attempt(workflow.id)

        self.assertEqual(updated.polling_attempts, 1)

    def test_increment_polling_attempt_multiple(self):
        workflow = self.service.create_workflow(po_id=42)
        self.service.increment_polling_attempt(workflow.id)
        self.service.increment_polling_attempt(workflow.id)
        updated = self.service.increment_polling_attempt(workflow.id)

        self.assertEqual(updated.polling_attempts, 3)

    def test_mark_confirmed(self):
        workflow = self.service.create_workflow(po_id=42)
        updated = self.service.mark_confirmed(workflow.id)

        self.assertEqual(updated.status, 'confirmed')

    def test_update_status_sets_last_poll_at_for_waiting(self):
        workflow = self.service.create_workflow(po_id=42)
        updated = self.service.update_status(
            workflow.id, PurchaseOrderWorkflow.Status.WAITING_CONFIRMATION
        )

        self.assertIsNotNone(updated.last_poll_at)
