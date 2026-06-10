from ai.agents.base_agent import BaseTool


class ForecastReadTool(BaseTool):
    name = 'forecast_read_tool'
    description = 'Reads forecast predictions.'

    def run(self, input: dict) -> dict:
        return {'forecasts': []}
