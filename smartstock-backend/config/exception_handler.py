from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from core.exceptions import (
    DuplicatePOError,
    ForecastingModelError,
    IllegalPOTransitionError,
    InsufficientStockError,
    StockNotFoundException,
    SupplierNotFoundException,
)

# Map internal DRF/Python exception types to safe, user-facing error type strings.
# This prevents leaking raw Python class names to API consumers.
# Domain exceptions (from core.exceptions) are preserved intentionally — the frontend
# relies on these for error handling.
_ERROR_TYPE_MAP = {
    'PermissionDenied': 'Forbidden',
    'NotFound': 'NotFound',
    'NotAuthenticated': 'AuthenticationRequired',
    'AuthenticationFailed': 'AuthenticationFailed',
    'Throttled': 'RateLimited',
}

# Domain exception types that are intentionally kept in API responses
_DOMAIN_EXCEPTION_TYPES = {
    'StockNotFoundException',
    'InsufficientStockError',
    'DuplicatePOError',
    'IllegalPOTransitionError',
    'ForecastingModelError',
    'SupplierNotFoundException',
}


def _sanitize_error_type(exc) -> str:
    """Return a safe, user-facing error type string.

    Domain exceptions (from core.exceptions) are preserved as-is because the
    frontend depends on them. Standard Django/DRF exceptions are mapped to
    generic strings to avoid leaking internal class names.
    """
    exc_name = type(exc).__name__
    if exc_name in _DOMAIN_EXCEPTION_TYPES:
        return exc_name
    return _ERROR_TYPE_MAP.get(exc_name, 'ServerError')


def _error_response(msg, exc_type, code):
    return {
        'status': 'error',
        'error': exc_type,
        'message': msg,
        'code': code,
    }


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is not None:
        detail = response.data
        status_code = response.status_code

        # CookieTokenRefreshSerializer missing cookie → 401, not 422
        if status_code == 422 or status_code == 400:
            if isinstance(detail, dict):
                has_cookie_msg = any(
                    'cookie' in str(v).lower()
                    if isinstance(v, str)
                    else any('cookie' in str(item).lower() for item in v if isinstance(item, str))
                    for v in detail.values()
                )
                if ('refresh' in detail and has_cookie_msg) or (
                    'non_field_errors' in detail and has_cookie_msg
                ):
                    msg = 'Refresh token not found in cookies.'
                    return Response(
                        {
                            'status': 'error',
                            'error': 'AuthenticationFailed',
                            'message': msg,
                            'code': 401,
                        },
                        status=401,
                    )

        if status_code == 404:
            msg = ''
            if isinstance(detail, dict):
                msg = detail.get('detail', '') or str(detail)
            elif isinstance(detail, str):
                msg = detail
            return Response(
                _error_response(msg, 'NotFound', status_code),
                status=status_code,
            )

        if status_code in (401, 403):
            msg = ''
            if isinstance(detail, dict):
                msg = detail.get('detail', '') or str(detail)
            elif isinstance(detail, str):
                msg = detail
            return Response(
                _error_response(msg, _sanitize_error_type(exc), status_code),
                status=status_code,
            )

        if status_code in (409, 400):
            is_duplicate = False
            if isinstance(detail, dict):
                for val in detail.values():
                    if isinstance(val, list) and any(
                        'already exists' in str(v).lower() for v in val
                    ):
                        is_duplicate = True
                        break
                    if isinstance(val, str) and 'already exists' in val.lower():
                        is_duplicate = True
                        break
            if is_duplicate or status_code == 409:
                msg = str(detail) if isinstance(detail, str) else detail.get('detail', '')
                return Response(
                    _error_response(msg, 'DuplicateEntry', 409),
                    status=409,
                )

        if status_code == 422 or status_code == 400:
            fields = {}
            if isinstance(detail, dict):
                for k, v in detail.items():
                    if isinstance(v, list):
                        fields[k] = [str(e) for e in v]
                    elif isinstance(v, str):
                        fields[k] = [v]
                    else:
                        fields[k] = [str(v)]
            elif isinstance(detail, str):
                fields = {'detail': [detail]}
            else:
                fields = {'detail': [str(detail)]}

            return Response(
                {
                    'status': 'error',
                    'error': 'ValidationError',
                    'message': 'Validation failed.',
                    'code': 422,
                    'fields': fields,
                },
                status=422,
            )
        return response

    if isinstance(exc, DjangoValidationError):
        return Response(
            {
                'status': 'error',
                'error': 'ValidationError',
                'message': 'Validation failed.',
                'code': 422,
                'fields': {'detail': exc.messages if hasattr(exc, 'messages') else [str(exc)]},
            },
            status=422,
        )

    if isinstance(exc, IntegrityError):
        msg = str(exc)
        if 'unique' in msg.lower() or 'duplicate' in msg.lower():
            return Response(
                _error_response('A record with this value already exists.', 'IntegrityError', 409),
                status=409,
            )

    STATUS_MAP = {
        StockNotFoundException: 404,
        InsufficientStockError: 409,
        DuplicatePOError: 409,
        IllegalPOTransitionError: 409,
        ForecastingModelError: 500,
        SupplierNotFoundException: 404,
    }
    status_code = STATUS_MAP.get(type(exc), 500)
    return Response(
        _error_response(str(exc), _sanitize_error_type(exc), status_code),
        status=status_code,
    )
