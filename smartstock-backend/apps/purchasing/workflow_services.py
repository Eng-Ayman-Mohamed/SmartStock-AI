import logging

from django.utils import timezone

from .repositories import PurchaseOrderWorkflowRepository
from .workflow_models import PurchaseOrderWorkflow

logger = logging.getLogger(__name__)


class PurchaseOrderWorkflowService:
    def __init__(self, repo=None):
        self.repo = repo or PurchaseOrderWorkflowRepository()

    def create_workflow(self, po_id: int) -> PurchaseOrderWorkflow:
        return self.repo.create(
            {
                "purchase_order_id": po_id,
                "status": PurchaseOrderWorkflow.Status.DRAFT,
            }
        )

    def get_workflow(self, po_id: int) -> PurchaseOrderWorkflow | None:
        return self.repo.get_by_po_id(po_id)

    def get_workflow_by_id(self, workflow_id: int) -> PurchaseOrderWorkflow:
        return self.repo.get_by_id(workflow_id)

    def update_status(
        self,
        workflow_id: int,
        status: str,
        *,
        message_id: str | None = None,
        error_message: str | None = None,
    ) -> PurchaseOrderWorkflow:
        update_data: dict = {"status": status}
        if message_id is not None:
            update_data["message_id"] = message_id
        if error_message is not None:
            update_data["error_message"] = error_message
        if status == PurchaseOrderWorkflow.Status.WAITING_CONFIRMATION:
            update_data["last_poll_at"] = timezone.now()
        return self.repo.update(workflow_id, update_data)

    def increment_polling_attempt(self, workflow_id: int) -> PurchaseOrderWorkflow:
        workflow = self.repo.get_by_id(workflow_id)
        return self.repo.update(
            workflow_id,
            {
                "polling_attempts": workflow.polling_attempts + 1,
                "last_poll_at": timezone.now(),
            },
        )

    def mark_confirmed(self, workflow_id: int) -> PurchaseOrderWorkflow:
        return self.repo.update(
            workflow_id,
            {
                "status": PurchaseOrderWorkflow.Status.CONFIRMED,
            },
        )
