from ai.agents.base_agent import BaseTool


class PODraftTool(BaseTool):
    name = 'po_draft_tool'
    description = 'Generates a formal Purchase Order for a given SKU and quantity.'

    def run(self, input: dict) -> dict:
        return {'po_id': None, 'status': 'draft'}
