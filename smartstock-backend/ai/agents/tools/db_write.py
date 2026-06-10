from ai.agents.base_agent import BaseTool


class DBWriteTool(BaseTool):
    name = 'db_write_tool'
    description = 'Writes data to the database.'

    def run(self, input: dict) -> dict:
        return {'status': 'written'}
