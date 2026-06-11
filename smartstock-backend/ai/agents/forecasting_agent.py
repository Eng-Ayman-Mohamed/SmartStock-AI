from ai.observability.langfuse import trace_agent_run


class ForecastingAgent:
    def run(self, context: dict | None = None) -> dict:
        payload = context or {}
        output = {'agent': 'forecasting_agent', 'status': 'not_implemented'}
        trace_agent_run('forecasting_agent', payload, output, [])
        return output
