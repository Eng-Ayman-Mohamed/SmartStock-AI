from ai.agents.base_agent import BaseTool


class DBUpdateTool(BaseTool):
    name = 'db_update_tool'
    description = 'Updates inventory status in the database.'

    def run(self, input: dict) -> dict:
        return {'status': 'updated'}
