from ai.agents.base_agent import BaseTool
from apps.forecasting.services import ForecastingService


class ForecastReadTool(BaseTool):
    name = 'forecast_read_tool'
    description = 'Reads forecast predictions.'

    def __init__(self, service=None):
        self.service = service or ForecastingService()

    def run(self, input: dict) -> dict:
        product_id = int(input['product_id'])
        forecast_days = int(input.get('forecast_days') or 7)
        return self.service.get_decision_forecast_data(product_id, forecast_days)
