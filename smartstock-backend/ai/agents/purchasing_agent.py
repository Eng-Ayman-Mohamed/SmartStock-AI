import logging
import time

from ai.agents.tools.confirmation_listener import ConfirmationListenerTool
from ai.agents.tools.email_send import EmailSendTool
from ai.agents.tools.po_draft import PODraftTool
from ai.observability.langfuse import trace_agent_run
from apps.purchasing.services import PurchasingService
from apps.purchasing.workflow_models import PurchaseOrderWorkflow
from apps.purchasing.workflow_services import PurchaseOrderWorkflowService

logger = logging.getLogger(__name__)


class PurchasingAgent:
    """End-to-end purchasing workflow agent with HITL approval, email dispatch,
    confirmation polling with exponential backoff, and status tracking.

    Status flow:
        DRAFT -> PENDING_APPROVAL -> APPROVED -> EMAIL_SENT -> WAITING_CONFIRMATION -> CONFIRMED

    Failure states: REJECTED, FAILED, TIMEOUT
    """

    def __init__(
        self,
        po_draft_tool=None,
        email_send_tool=None,
        confirmation_tool=None,
        purchasing_service=None,
        workflow_service=None,
        *,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        max_attempts: int = 10,
        sleep_fn=None,
    ):
        self.po_draft_tool = po_draft_tool or PODraftTool()
        self.email_send_tool = email_send_tool or EmailSendTool()
        self.confirmation_tool = confirmation_tool or ConfirmationListenerTool()
        self.purchasing_service = purchasing_service or PurchasingService()
        self.workflow_service = workflow_service or PurchaseOrderWorkflowService()
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self._sleep_fn = sleep_fn or time.sleep

    def run(self, context: dict) -> dict:
        """Execute the full purchasing workflow.

        Context keys:
            sku_id: int - SKU to purchase
            quantity: int - quantity needed
            supplier_id: int - supplier to order from
            user_id: int - requesting user ID
            agent_reasoning: str - why this order is needed
            auto_approve: bool - skip HITL gate (for testing/integration)

        Returns:
            dict with workflow result, status, and PO details.
        """
        trace_spans = []
        try:
            result = self._execute_workflow(context, trace_spans)
        except Exception as e:
            logger.exception("PurchasingAgent workflow failed")
            result = {
                "agent": "purchasing_agent",
                "status": "failed",
                "error": str(e),
            }
        trace_agent_run("purchasing_agent", context, result, trace_spans)
        return result

    def _execute_workflow(self, context: dict, trace_spans: list) -> dict:
        # Step 1: Create draft PO
        draft_result = self._run_tool(
            self.po_draft_tool,
            {
                "sku_id": context["sku_id"],
                "quantity": context["quantity"],
                "supplier_id": context["supplier_id"],
                "user_id": context.get("user_id"),
                "agent_reasoning": context.get("agent_reasoning", ""),
                "total_cost": context.get("total_cost", "0.00"),
            },
            trace_spans,
        )

        if draft_result.get("status") == "failed" or not draft_result.get("po_id"):
            return {
                "agent": "purchasing_agent",
                "status": "failed",
                "error": draft_result.get("error", "Failed to create draft PO"),
                "step": "draft",
            }

        po_id = draft_result["po_id"]

        # Create workflow record
        workflow = self.workflow_service.create_workflow(po_id)

        # Step 2: HITL Approval Gate
        approval_result = self._handle_approval_gate(
            po_id, workflow.id, context, trace_spans
        )
        if approval_result is not None:
            return approval_result

        # Step 3: Send email
        email_result = self._send_email(po_id, workflow.id, trace_spans)
        if email_result is not None:
            return email_result

        # Step 4: Poll for confirmation with exponential backoff
        confirm_result = self._poll_for_confirmation(po_id, workflow.id, trace_spans)
        return confirm_result

    def _handle_approval_gate(
        self,
        po_id: int,
        workflow_id: int,
        context: dict,
        trace_spans: list,
    ) -> dict | None:
        """Handle the HITL approval gate. Returns None if approved, or a result dict if rejected."""
        self.workflow_service.update_status(
            workflow_id, PurchaseOrderWorkflow.Status.PENDING_APPROVAL
        )

        user = context.get("user")

        if context.get("auto_approve"):
            if user is not None:
                self.purchasing_service.approve_po(po_id, user)
            self.workflow_service.update_status(
                workflow_id, PurchaseOrderWorkflow.Status.APPROVED
            )
            return None

        approval_callback = context.get("approval_callback")
        if approval_callback:
            approved = approval_callback(po_id)
            if not approved:
                self.purchasing_service.reject_po(po_id, user)
                self.workflow_service.update_status(
                    workflow_id, PurchaseOrderWorkflow.Status.REJECTED
                )
                self._run_tool(
                    self.po_draft_tool,
                    {"action": "trace", "step": "approval_rejected"},
                    trace_spans,
                )
                return {
                    "agent": "purchasing_agent",
                    "status": "rejected",
                    "po_id": po_id,
                    "workflow_id": workflow_id,
                    "message": "Human approval rejected. PO not sent.",
                }
            if user is not None:
                self.purchasing_service.approve_po(po_id, user)
            self.workflow_service.update_status(
                workflow_id, PurchaseOrderWorkflow.Status.APPROVED
            )
            return None

        # No auto_approve and no callback: return pending status for caller to handle
        return {
            "agent": "purchasing_agent",
            "status": "pending_approval",
            "po_id": po_id,
            "workflow_id": workflow_id,
            "message": "PO requires human approval before sending.",
        }

    def _send_email(
        self, po_id: int, workflow_id: int, trace_spans: list
    ) -> dict | None:
        """Send the PO email. Returns None on success, or a result dict on failure."""
        email_result = self._run_tool(
            self.email_send_tool,
            {"po_id": po_id},
            trace_spans,
        )

        if email_result.get("status") == "failed":
            self.purchasing_service.mark_failed(
                po_id, email_result.get("error", "Email dispatch failed")
            )
            self.workflow_service.update_status(
                workflow_id,
                PurchaseOrderWorkflow.Status.FAILED,
                error_message=email_result.get("error", "Email dispatch failed"),
            )
            return {
                "agent": "purchasing_agent",
                "status": "failed",
                "po_id": po_id,
                "workflow_id": workflow_id,
                "error": email_result.get("error", "Email dispatch failed"),
                "step": "email_send",
            }

        message_id = email_result.get("message_id")
        self.purchasing_service.mark_email_sent(po_id, message_id=message_id)
        self.workflow_service.update_status(
            workflow_id,
            PurchaseOrderWorkflow.Status.EMAIL_SENT,
            message_id=message_id,
        )
        self.purchasing_service.mark_waiting_confirmation(po_id)
        self.workflow_service.update_status(
            workflow_id, PurchaseOrderWorkflow.Status.WAITING_CONFIRMATION
        )
        return None

    def _poll_for_confirmation(
        self, po_id: int, workflow_id: int, trace_spans: list
    ) -> dict:
        """Poll for supplier confirmation using exponential backoff.

        Backoff schedule:
            attempt 0 -> wait initial_delay
            attempt 1 -> wait initial_delay * 2
            attempt 2 -> wait initial_delay * 4
            ...
            capped at max_delay
        """
        delay = self.initial_delay

        for attempt in range(self.max_attempts):
            self.workflow_service.increment_polling_attempt(workflow_id)

            self._sleep_fn(delay)

            poll_result = self._run_tool(
                self.confirmation_tool,
                {"po_id": po_id},
                trace_spans,
            )

            if poll_result.get("confirmed"):
                self.purchasing_service.mark_confirmed(po_id)
                self.workflow_service.mark_confirmed(workflow_id)
                return {
                    "agent": "purchasing_agent",
                    "status": "confirmed",
                    "po_id": po_id,
                    "workflow_id": workflow_id,
                    "polling_attempts": attempt + 1,
                }

            if poll_result.get("terminal"):
                terminal_status = poll_result.get("status", "failed")
                self.purchasing_service.mark_failed(
                    po_id, f"PO reached terminal status: {terminal_status}"
                )
                self.workflow_service.update_status(
                    workflow_id,
                    PurchaseOrderWorkflow.Status.FAILED,
                    error_message=f"PO reached terminal status: {terminal_status}",
                )
                return {
                    "agent": "purchasing_agent",
                    "status": "failed",
                    "po_id": po_id,
                    "workflow_id": workflow_id,
                    "error": f"PO reached terminal status: {terminal_status}",
                    "polling_attempts": attempt + 1,
                }

            delay = min(delay * 2, self.max_delay)

        # Max attempts exhausted
        self.purchasing_service.mark_timeout(po_id)
        self.workflow_service.update_status(
            workflow_id, PurchaseOrderWorkflow.Status.TIMEOUT
        )
        return {
            "agent": "purchasing_agent",
            "status": "timeout",
            "po_id": po_id,
            "workflow_id": workflow_id,
            "polling_attempts": self.max_attempts,
            "error": f"Confirmation not received after {self.max_attempts} attempts",
        }

    def _run_tool(self, tool, tool_input: dict, trace_spans: list) -> dict:
        started_at = time.time()
        output = tool.run(tool_input)
        trace_spans.append(
            {
                "name": getattr(tool, "name", tool.__class__.__name__),
                "input": tool_input,
                "output": output,
                "duration_ms": round((time.time() - started_at) * 1000),
            }
        )
        return output
