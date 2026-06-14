import logging

import pandas as pd
from pydantic import BaseModel, Field

from ai.agents.base_agent import BaseTool
from apps.forecasting.prophet_engine import ProphetEngine

logger = logging.getLogger(__name__)


class ProphetRunInput(BaseModel):
    sku_id: int = Field(..., description='SKU ID being forecast.')
    sku_code: str = Field('', description='SKU code for logging.')
    data: list = Field(..., description='Historical sales data as list of {ds, y} records.')
    periods: int = Field(30, description='Number of future days to forecast.')


class ProphetRunTool(BaseTool):
    name = 'prophet_run_tool'
    description = (
        'Runs the Prophet forecasting model on historical sales data. '
        'Returns a 30-day forecast with predicted_quantity, lower_bound, and upper_bound '
        'for each day. Falls back to a 7-day moving average if data is insufficient '
        'or Prophet is unavailable. The model_version field indicates which method was used.'
    )
    args_schema = ProphetRunInput

    def __init__(self, engine=None):
        self.engine = engine or ProphetEngine()

    def run(self, input: dict) -> dict:
        sku_id = int(input['sku_id'])
        sku_code = input.get('sku_code', '')
        raw_data = input.get('data', [])
        periods = int(input.get('periods', 30))

        if not raw_data:
            logger.warning(
                'No data provided for SKU %s (ID %d); using empty forecast',
                sku_code or sku_id,
                sku_id,
            )
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(raw_data)
            df['ds'] = pd.to_datetime(df['ds'])
            df['y'] = df['y'].astype(float)

        result = self.engine.predict(df, periods=periods)

        return {
            'sku_id': sku_id,
            'sku_code': sku_code,
            'forecast_days': len(result['results']),
            'results': result['results'],
            'model_version': result['model_version'],
            'forecast_method': result.get('forecast_method', 'unknown'),
            'mae': result.get('mae'),
            'mape': result.get('mape'),
        }
