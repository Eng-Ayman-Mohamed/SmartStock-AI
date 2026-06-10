from ai.agents.base_agent import BaseTool


class EmailSendTool(BaseTool):
    name = 'email_send_tool'
    description = 'Dispatches an email to a supplier.'

    def run(self, input: dict) -> dict:
        return {'status': 'sent'}
