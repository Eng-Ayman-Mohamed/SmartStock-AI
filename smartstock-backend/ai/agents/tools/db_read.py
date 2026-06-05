from ai.agents.base_agent import BaseTool


class DBReadTool(BaseTool):
    name = "db_read_tool"
    description = "Reads data from the database."

    def run(self, input: dict) -> dict:
        return {"data": []}
