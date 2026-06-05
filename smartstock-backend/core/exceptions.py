class StockNotFoundException(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class DuplicatePOError(Exception):
    pass


class ForecastingModelError(Exception):
    pass


class SupplierNotFoundException(Exception):
    pass
