from .repositories import ForecastingRepository
from .prophet_engine import ProphetEngine


class ForecastingService:
    def __init__(self):
        self.repo = ForecastingRepository()
        self.engine = ProphetEngine()

    def get_forecast(self, sku_id: int):
        return self.repo.get_by_sku(sku_id)

    def run_forecast(self):
        skus = self.repo.get_all_skus()
        results = []
        for sku in skus:
            predictions = self.engine.predict(sku)
            for pred in predictions:
                result = self.repo.create(pred)
                results.append(result)
        return results
