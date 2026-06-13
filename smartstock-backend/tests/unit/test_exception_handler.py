from unittest.mock import MagicMock

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from config.exception_handler import custom_exception_handler
from core.exceptions import (
    DuplicatePOError,
    ForecastingModelError,
    InsufficientStockError,
    StockNotFoundException,
    SupplierNotFoundException,
)


class ExceptionHandlerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def _call_handler(self, exc, view=None):
        context = {'view': view or MagicMock()}
        request = self.factory.get('/')
        return custom_exception_handler(exc, context)


class StockNotFoundExceptionTest(ExceptionHandlerTest):
    def test_stock_not_found_returns_404(self):
        exc = StockNotFoundException('SKU-123 not found')
        response = self._call_handler(exc)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'StockNotFoundException')
        self.assertEqual(response.data['code'], 404)

    def test_stock_not_found_message_preserved(self):
        exc = StockNotFoundException('SKU-999 not found')
        response = self._call_handler(exc)
        self.assertIn('SKU-999', str(response.data['message']))


class InsufficientStockExceptionTest(ExceptionHandlerTest):
    def test_insufficient_stock_returns_409(self):
        exc = InsufficientStockError('Only 5 available, requested 10')
        response = self._call_handler(exc)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['error'], 'InsufficientStockError')

    def test_insufficient_stock_message_preserved(self):
        exc = InsufficientStockError('Not enough stock')
        response = self._call_handler(exc)
        self.assertIn('Not enough stock', str(response.data['message']))


class DuplicatePOErrorTest(ExceptionHandlerTest):
    def test_duplicate_po_returns_409(self):
        exc = DuplicatePOError('PO already exists for this SKU')
        response = self._call_handler(exc)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['error'], 'DuplicatePOError')


class ForecastingModelErrorTest(ExceptionHandlerTest):
    def test_forecasting_model_error_returns_500(self):
        exc = ForecastingModelError('Model training failed')
        response = self._call_handler(exc)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['error'], 'ForecastingModelError')


class SupplierNotFoundExceptionTest(ExceptionHandlerTest):
    def test_supplier_not_found_returns_404(self):
        exc = SupplierNotFoundException('Supplier 99 not found')
        response = self._call_handler(exc)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'SupplierNotFoundException')


class GenericExceptionHandlerTest(ExceptionHandlerTest):
    def test_unregistered_exception_returns_500(self):
        exc = ValueError('Something went wrong')
        response = self._call_handler(exc)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['error'], 'ValueError')
        self.assertIn('Something went wrong', str(response.data['message']))


class DRFExceptionHandlerStringDetailTest(ExceptionHandlerTest):
    def test_404_with_string_detail(self):
        from rest_framework.exceptions import NotFound
        from rest_framework.views import exception_handler

        class Fake404View:
            def get(self, request):
                raise NotFound('Resource not found')

        exc = NotFound('Resource not found')
        exc.detail = 'Resource not found'
        context = {'view': MagicMock()}
        response = custom_exception_handler(exc, context)
        self.assertEqual(response.status_code, 404)

    def test_401_with_string_detail(self):
        from rest_framework.exceptions import AuthenticationFailed

        exc = AuthenticationFailed('Authentication required')
        exc.detail = 'Authentication required'
        context = {'view': MagicMock()}
        response = custom_exception_handler(exc, context)
        self.assertEqual(response.status_code, 401)

    def test_validation_error_422_format(self):
        from rest_framework.exceptions import ValidationError

        exc = ValidationError({'field1': ['error a', 'error b']})
        response = custom_exception_handler(exc, MagicMock())
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data['error'], 'ValidationError')
        self.assertIn('fields', response.data)