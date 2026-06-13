from ai.agents.base_agent import BaseTool
from apps.purchasing.services import PurchasingService


class ConfirmationListenerTool(BaseTool):
    name = 'confirmation_listener_tool'
    description = 'Checks if a supplier has confirmed the Purchase Order. Non-blocking poll.'

    def __init__(self, service=None):
        self.service = service or PurchasingService()

    def run(self, input: dict) -> dict:
        po_id = int(input['po_id'])
        return self.service.check_confirmation(po_id)
