from pydantic import BaseModel, Field

from ai.agents.base_agent import BaseTool
from apps.forecasting.services import ForecastingService


class ForecastReadBySKUInput(BaseModel):
    sku_id: int = Field(..., description='SKU ID to forecast.')
    forecast_days: int = Field(7, description='Forecast horizon in days.')


class ForecastReadBySKUTool(BaseTool):
    name = 'forecast_read_by_sku_tool'
    description = 'Reads forecast predictions for a specific SKU.'
    args_schema = ForecastReadBySKUInput

    def __init__(self, service=None):
        self.service = service or ForecastingService()

    def run(self, input: dict) -> dict:
        sku_id = int(input['sku_id'])
        forecast_days = int(input.get('forecast_days') or 7)
        return self.service.get_decision_forecast_data_by_sku(sku_id, forecast_days)
