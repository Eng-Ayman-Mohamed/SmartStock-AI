import logging

from pydantic import BaseModel, Field

from ai.agents.base_agent import BaseTool
from apps.forecasting.repositories import ForecastingRepository

logger = logging.getLogger(__name__)


class ForecastResultItem(BaseModel):
    forecast_date: str = Field(..., description='Date of forecast (YYYY-MM-DD).')
    predicted_quantity: float = Field(..., description='Predicted quantity.')
    lower_bound: float | None = Field(None, description='Lower confidence bound.')
    upper_bound: float | None = Field(None, description='Upper confidence bound.')


class ForecastDBWriteInput(BaseModel):
    sku_id: int = Field(..., description='SKU ID to write forecast for.')
    sku_code: str = Field('', description='SKU code for logging.')
    results: list[ForecastResultItem] = Field(..., description='Forecast results to persist.')
    model_version: str = Field('', description='Model version identifier.')
    mae: float | None = Field(None, description='Mean absolute error.')
    mape: float | None = Field(None, description='Mean absolute percentage error.')


class ForecastDBWriteTool(BaseTool):
    name = 'forecast_db_write_tool'
    description = (
        'Writes forecast results to the database for a given SKU. '
        'Uses upsert semantics so running twice is idempotent. '
        'Skips if a forecast already exists for today (idempotency check).'
    )
    args_schema = ForecastDBWriteInput

    def __init__(self, repo=None):
        self.repo = repo or ForecastingRepository()

    def run(self, input: dict) -> dict:
        sku_id = int(input['sku_id'])
        sku_code = input.get('sku_code', '')
        results = input.get('results', [])
        model_version = input.get('model_version', '')
        mae = input.get('mae')
        mape = input.get('mape')

        if self.repo.has_todays_forecast(sku_id):
            logger.info(
                'Skipping SKU %s (ID %d) — forecast already exists for today',
                sku_code or sku_id,
                sku_id,
            )
            return {
                'sku_id': sku_id,
                'sku_code': sku_code or '',
                'status': 'skipped',
                'reason': 'todays_forecast_exists',
                'records_written': 0,
            }

        written = 0
        for item in results:
            self.repo.upsert(
                sku_id=sku_id,
                forecast_date=item['forecast_date'],
                predicted_quantity=item['predicted_quantity'],
                lower_bound=item.get('lower_bound'),
                upper_bound=item.get('upper_bound'),
                mae=mae,
                mape=mape,
                model_version=model_version,
            )
            written += 1

        logger.info(
            'Wrote %d forecast records for SKU %s (ID %d) using %s',
            written,
            sku_code or sku_id,
            sku_id,
            model_version,
        )
        return {
            'sku_id': sku_id,
            'sku_code': sku_code or '',
            'status': 'written',
            'records_written': written,
            'model_version': model_version,
        }
