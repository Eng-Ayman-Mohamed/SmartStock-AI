import logging

import pandas as pd
from pydantic import BaseModel, Field

from ai.agents.base_agent import BaseTool
from apps.forecasting.ingestion import prepare_forecast_dataframe
from apps.forecasting.repositories import ForecastingRepository

logger = logging.getLogger(__name__)


class ForecastDBReadInput(BaseModel):
    sku_id: int = Field(..., description='SKU ID to read historical sales data for.')
    sku_code: str = Field('', description='SKU code for logging purposes.')


class ForecastDBReadTool(BaseTool):
    name = 'forecast_db_read_tool'
    description = (
        'Reads historical sales data for a given SKU. '
        'Returns cleaned daily sales with ds (date) and y (quantity) columns. '
        'If data is insufficient (< 30 records), returns an empty data signal '
        'so the agent can still proceed with a fallback forecast.'
    )
    args_schema = ForecastDBReadInput

    def __init__(self, repo=None):
        self.repo = repo or ForecastingRepository()

    def run(self, input: dict) -> dict:
        sku_id = int(input['sku_id'])
        sku_code = input.get('sku_code', '')

        df = prepare_forecast_dataframe(sku_id)

        if df is None or df.empty:
            logger.warning('No data returned for SKU %s (ID %d)', sku_code or sku_id, sku_id)
            return {
                'sku_id': sku_id,
                'sku_code': sku_code or '',
                'has_data': False,
                'record_count': 0,
                'message': 'Insufficient or missing historical sales data.',
            }

        records = self._df_to_records(df)
        return {
            'sku_id': sku_id,
            'sku_code': sku_code or '',
            'has_data': True,
            'record_count': len(records),
            'data': records,
            'message': f'Loaded {len(records)} daily sales records.',
        }

    @staticmethod
    def _df_to_records(df: pd.DataFrame) -> list[dict]:
        return [
            {'ds': str(row['ds'].date() if hasattr(row['ds'], 'date') else row['ds']), 'y': float(row['y'])}
            for _, row in df.iterrows()
        ]
