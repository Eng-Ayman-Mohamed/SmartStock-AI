from pydantic import BaseModel, Field

from ai.agents.base_agent import BaseTool
from apps.forecasting.services import ForecastingService


class ForecastReadInput(BaseModel):
    product_id: int = Field(..., description='Product ID to forecast.')
    forecast_days: int = Field(7, description='Forecast horizon in days.')


class ForecastReadTool(BaseTool):
    name = 'forecast_read_tool'
    description = 'Reads forecast predictions.'
    args_schema = ForecastReadInput

    def __init__(self, service=None):
        self.service = service or ForecastingService()

    def run(self, input: dict) -> dict:
        product_id = int(input['product_id'])
        forecast_days = int(input.get('forecast_days') or 7)
        return self.service.get_decision_forecast_data(product_id, forecast_days)
