from ai.agents.base_agent import BaseTool
from apps.purchasing.services import PurchasingService


class EmailSendTool(BaseTool):
    name = 'email_send_tool'
    description = 'Sends a Purchase Order email to the supplier for confirmation.'

    def __init__(self, service=None):
        self.service = service or PurchasingService()

    def run(self, input: dict) -> dict:
        po_id = int(input['po_id'])
        return self.service.send_po_email(po_id)
