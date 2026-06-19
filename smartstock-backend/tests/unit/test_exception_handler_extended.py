from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.response import Response

from config.exception_handler import _error_response, custom_exception_handler


class ErrorReponseHelperTest(TestCase):
    def test_error_response_structure(self):
        result = _error_response('Not found', 'NotFound', 404)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], 'NotFound')
        self.assertEqual(result['message'], 'Not found')
        self.assertEqual(result['code'], 404)


class CookieTokenRefreshTest(TestCase):
    def test_422_with_cookie_refresh_message_returns_401(self):
        context = {'view': MagicMock()}

        class FakeExc:
            pass

        response = MagicMock()
        response.status_code = 422
        response.data = {
            'refresh': ['cookie token not found'],
            'non_field_errors': [],
        }

        with patch('config.exception_handler.drf_exception_handler', return_value=response):
            result = custom_exception_handler(FakeExc(), context)

        self.assertEqual(result.status_code, 401)
        self.assertIn('Refresh token not found in cookies', str(result.data['message']))

    def test_400_with_cookie_in_non_field_errors(self):
        context = {'view': MagicMock()}

        class FakeExc:
            pass

        response = MagicMock()
        response.status_code = 400
        response.data = {
            'non_field_errors': ['cookie is missing'],
        }

        with patch('config.exception_handler.drf_exception_handler', return_value=response):
            result = custom_exception_handler(FakeExc(), context)

        self.assertEqual(result.status_code, 401)

    def test_422_without_cookie_not_rewritten(self):
        context = {'view': MagicMock()}

        class FakeExc:
            pass

        response = MagicMock()
        response.status_code = 422
        response.data = {'field1': ['error']}

        with patch('config.exception_handler.drf_exception_handler', return_value=response):
            result = custom_exception_handler(FakeExc(), context)

        self.assertEqual(result.status_code, 422)
        self.assertEqual(result.data['error'], 'ValidationError')


class ConflictHandlingTest(TestCase):
    def test_409_with_already_exists_returns_409(self):
        context = {'view': MagicMock()}

        class FakeExc:
            pass

        response = MagicMock()
        response.status_code = 409
        response.data = {'name': ['this name already exists']}

        with patch('config.exception_handler.drf_exception_handler', return_value=response):
            result = custom_exception_handler(FakeExc(), context)

        self.assertEqual(result.status_code, 409)

    def test_400_with_already_exists_returns_409(self):
        context = {'view': MagicMock()}

        class FakeExc:
            pass

        response = MagicMock()
        response.status_code = 400
        response.data = {'sku': ['sku already exists']}

        with patch('config.exception_handler.drf_exception_handler', return_value=response):
            result = custom_exception_handler(FakeExc(), context)

        self.assertEqual(result.status_code, 409)

    def test_400_with_string_already_exists(self):
        context = {'view': MagicMock()}

        class FakeExc:
            pass

        response = MagicMock()
        response.status_code = 400
        response.data = {'field': 'record already exists'}

        with patch('config.exception_handler.drf_exception_handler', return_value=response):
            result = custom_exception_handler(FakeExc(), context)

        self.assertEqual(result.status_code, 409)


class ValidationError422HandlingTest(TestCase):
    def test_422_with_dict_detail(self):
        context = {'view': MagicMock()}

        class FakeExc:
            pass

        response = MagicMock()
        response.status_code = 422
        response.data = {'field1': ['err1', 'err2'], 'field2': 'single err'}

        with patch('config.exception_handler.drf_exception_handler', return_value=response):
            result = custom_exception_handler(FakeExc(), context)

        self.assertEqual(result.status_code, 422)
        self.assertIn('fields', result.data)

    def test_422_with_string_detail(self):
        context = {'view': MagicMock()}

        class FakeExc:
            pass

        response = MagicMock()
        response.status_code = 422
        response.data = 'bad input'

        with patch('config.exception_handler.drf_exception_handler', return_value=response):
            result = custom_exception_handler(FakeExc(), context)

        self.assertEqual(result.status_code, 422)
        self.assertIn('fields', result.data)


class DjangoValidationErrorTest(TestCase):
    def test_django_validation_error_returns_422(self):
        from django.core.exceptions import ValidationError as DjangoVE

        context = {'view': MagicMock()}
        exc = DjangoVE(['field is required', 'another error'])

        with patch('config.exception_handler.drf_exception_handler', return_value=None):
            result = custom_exception_handler(exc, context)

        self.assertEqual(result.status_code, 422)
        self.assertEqual(result.data['error'], 'ValidationError')

    def test_django_validation_error_no_messages_attr(self):
        from django.core.exceptions import ValidationError as DjangoVE

        context = {'view': MagicMock()}
        exc = DjangoVE('simple error')

        with patch('config.exception_handler.drf_exception_handler', return_value=None):
            result = custom_exception_handler(exc, context)

        self.assertEqual(result.status_code, 422)


class IntegrityErrorTest(TestCase):
    def test_unique_integrity_error_returns_409(self):
        from django.db import IntegrityError as DjangoIntegrityError

        context = {'view': MagicMock()}
        exc = DjangoIntegrityError('UNIQUE constraint failed: table.name')

        with patch('config.exception_handler.drf_exception_handler', return_value=None):
            result = custom_exception_handler(exc, context)

        self.assertEqual(result.status_code, 409)
        self.assertEqual(result.data['error'], 'IntegrityError')

    def test_duplicate_integrity_error_returns_409(self):
        from django.db import IntegrityError as DjangoIntegrityError

        context = {'view': MagicMock()}
        exc = DjangoIntegrityError('duplicate key value violates unique constraint')

        with patch('config.exception_handler.drf_exception_handler', return_value=None):
            result = custom_exception_handler(exc, context)

        self.assertEqual(result.status_code, 409)

    def test_non_unique_integrity_error_not_caught(self):
        from django.db import IntegrityError as DjangoIntegrityError

        context = {'view': MagicMock()}
        exc = DjangoIntegrityError('foreign key violation')

        with patch('config.exception_handler.drf_exception_handler', return_value=None):
            result = custom_exception_handler(exc, context)

        self.assertEqual(result.status_code, 500)


class IllegalPOTransitionTest(TestCase):
    def test_illegal_po_transition_returns_409(self):
        from core.exceptions import IllegalPOTransitionError

        context = {'view': MagicMock()}
        exc = IllegalPOTransitionError('Cannot transition from sent to draft')

        with patch('config.exception_handler.drf_exception_handler', return_value=None):
            result = custom_exception_handler(exc, context)

        self.assertEqual(result.status_code, 409)
        self.assertEqual(result.data['error'], 'IllegalPOTransitionError')
