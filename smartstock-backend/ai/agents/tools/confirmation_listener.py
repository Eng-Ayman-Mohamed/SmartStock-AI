from ai.agents.base_agent import BaseTool


class ConfirmationListenerTool(BaseTool):
    name = "confirmation_listener_tool"
    description = "Polls for supplier reply."

    def run(self, input: dict) -> dict:
        return {"confirmed": False}
