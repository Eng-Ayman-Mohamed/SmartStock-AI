from ai.observability.langfuse import trace_agent_run


class PurchasingAgent:
    def run(self, context: dict) -> dict:
        output = {'agent': 'purchasing_agent', 'action': 'draft_po'}
        trace_agent_run('purchasing_agent', context, output, [])
        return output
