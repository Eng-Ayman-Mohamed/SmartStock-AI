from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from core.exceptions import (
    StockNotFoundException,
    InsufficientStockError,
    DuplicatePOError,
    ForecastingModelError,
    SupplierNotFoundException,
)


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    STATUS_MAP = {
        StockNotFoundException: 404,
        InsufficientStockError: 409,
        DuplicatePOError: 409,
        ForecastingModelError: 500,
        SupplierNotFoundException: 404,
    }
    status_code = STATUS_MAP.get(type(exc), 500)
    return Response(
        {"error": str(exc), "type": type(exc).__name__},
        status=status_code,
    )
