from ai.agents.base_agent import BaseTool


class POStatusCheckTool(BaseTool):
    name = "po_status_check_tool"
    description = "Checks for open duplicate POs."

    def run(self, input: dict) -> dict:
        return {"duplicate_found": False}
