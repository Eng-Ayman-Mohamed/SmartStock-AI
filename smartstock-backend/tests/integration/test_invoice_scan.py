from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser


class InvoiceScanEndpointTests(APITestCase):
    """Integration tests for /api/ai/invoice-scan/"""

    @classmethod
    def setUpTestData(cls):
        cls.manager = CustomUser.objects.create_user(
            email='manager@test.com',
            username='manager@test.com',
            password='StrongPass123!',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='viewer@test.com',
            username='viewer@test.com',
            password='StrongPass123!',
            role='viewer',
        )

    def _url(self, path=''):
        return f'/api/ai/invoice-scan/{path}'

    def _auth(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def _jpg_file(self, name='invoice.jpg', content=b'fake-jpeg-data'):
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile(name, content, content_type='image/jpeg')

    # --- Auth & RBAC ---

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_unauthenticated_returns_401(self, mock_svc):
        response = self.client.post(self._url(), {'file': self._jpg_file()})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_viewer_returns_403(self, mock_svc):
        self._auth(self.viewer)
        response = self.client.post(self._url(), {'file': self._jpg_file()})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Validation ---

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_missing_file_returns_422(self, mock_svc):
        self._auth(self.manager)
        response = self.client.post(self._url(), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_wrong_content_type_returns_422(self, mock_svc):
        from django.core.files.uploadedfile import SimpleUploadedFile

        bad_file = SimpleUploadedFile('bad.txt', b'text', content_type='text/plain')
        self._auth(self.manager)
        response = self.client.post(self._url(), {'file': bad_file})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_file_too_large_returns_422(self, mock_svc):
        from django.core.files.uploadedfile import SimpleUploadedFile

        big_file = SimpleUploadedFile(
            'big.jpg', b'x' * (5 * 1024 * 1024 + 1), content_type='image/jpeg'
        )
        self._auth(self.manager)
        response = self.client.post(self._url(), {'file': big_file})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    # --- Success ---

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_scan_returns_200_with_data(self, mock_svc_cls):
        mock_instance = mock_svc_cls.return_value
        mock_instance.scan_invoice.return_value = {
            'scan_id': 1,
            'status': 'extracted',
            'extracted_data': {
                'product_name': 'Widget',
                'sku_code': 'SKU-001',
                'quantity_received': 10,
                'unit_price': 5.99,
                'supplier_name': 'Acme',
            },
            'confidence': {'product_name': 0.95, 'sku_code': 0.98},
            'missing_fields': [],
            'failure_reason': '',
            'confirmed_data': {},
            'is_confirmed': False,
        }
        self._auth(self.manager)
        response = self.client.post(self._url(), {'file': self._jpg_file()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['scan_id'], 1)
        self.assertEqual(response.data['data']['status'], 'extracted')
        mock_instance.scan_invoice.assert_called_once()

    # --- Timeout ---

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_timeout_returns_504(self, mock_svc_cls):
        from apps.ingestion.services import InvoiceExtractionTimeout

        mock_instance = mock_svc_cls.return_value
        mock_instance.scan_invoice.side_effect = InvoiceExtractionTimeout('Timed out')
        self._auth(self.manager)
        response = self.client.post(self._url(), {'file': self._jpg_file()})
        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)

    # --- Vision provider not supported ---

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_provider_no_vision_returns_501(self, mock_svc_cls):
        from apps.ingestion.services import InvoiceExtractionMalformed

        mock_instance = mock_svc_cls.return_value
        mock_instance.scan_invoice.side_effect = InvoiceExtractionMalformed(
            'Model does not support vision'
        )
        self._auth(self.manager)
        response = self.client.post(self._url(), {'file': self._jpg_file()})
        self.assertEqual(response.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    # --- Malformed extraction ---

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_malformed_extraction_returns_422(self, mock_svc_cls):
        from apps.ingestion.services import InvoiceExtractionMalformed

        mock_instance = mock_svc_cls.return_value
        mock_instance.scan_invoice.side_effect = InvoiceExtractionMalformed('Bad JSON')
        self._auth(self.manager)
        response = self.client.post(self._url(), {'file': self._jpg_file()})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)


class InvoiceScanConfirmTests(APITestCase):
    """Integration tests for POST /api/ai/invoice-scan/confirm/"""

    @classmethod
    def setUpTestData(cls):
        cls.manager = CustomUser.objects.create_user(
            email='manager@test.com',
            username='manager@test.com',
            password='StrongPass123!',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='viewer@test.com',
            username='viewer@test.com',
            password='StrongPass123!',
            role='viewer',
        )

    def _url(self):
        return '/api/ai/invoice-scan/confirm/'

    def _auth(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_confirm_success(self, mock_svc_cls):
        mock_instance = mock_svc_cls.return_value
        mock_instance.confirm_scan.return_value = {
            'scan_id': 1,
            'status': 'confirmed',
            'inventory_result': {'success': True},
        }
        self._auth(self.manager)
        payload = {
            'scan_id': 1,
            'confirmed_data': {
                'product_name': 'Widget',
                'sku_code': 'SKU-001',
                'quantity_received': 10,
                'unit_price': 5.99,
                'supplier_name': 'Acme',
            },
        }
        response = self.client.post(self._url(), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'confirmed')

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_confirm_missing_required_fields_returns_422(self, mock_svc_cls):
        self._auth(self.manager)
        payload = {'scan_id': 1, 'confirmed_data': {'product_name': 'Widget'}}
        response = self.client.post(self._url(), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_confirm_already_confirmed_returns_409(self, mock_svc_cls):
        from apps.ingestion.services import InvoiceAlreadyConfirmed

        mock_instance = mock_svc_cls.return_value
        mock_instance.confirm_scan.side_effect = InvoiceAlreadyConfirmed('Already confirmed')
        self._auth(self.manager)
        payload = {
            'scan_id': 1,
            'confirmed_data': {
                'product_name': 'Widget',
                'sku_code': 'SKU-001',
                'quantity_received': 10,
                'unit_price': 5.99,
                'supplier_name': 'Acme',
            },
        }
        response = self.client.post(self._url(), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_confirm_not_found_returns_404(self, mock_svc_cls):
        from django.core.exceptions import ObjectDoesNotExist

        mock_instance = mock_svc_cls.return_value
        mock_instance.confirm_scan.side_effect = ObjectDoesNotExist
        self._auth(self.manager)
        payload = {
            'scan_id': 999,
            'confirmed_data': {
                'product_name': 'Widget',
                'sku_code': 'SKU-001',
                'quantity_received': 10,
                'unit_price': 5.99,
                'supplier_name': 'Acme',
            },
        }
        response = self.client.post(self._url(), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_confirm_permission_error_returns_403(self, mock_svc_cls):
        mock_instance = mock_svc_cls.return_value
        mock_instance.confirm_scan.side_effect = PermissionError('Not your scan')
        self._auth(self.manager)
        payload = {
            'scan_id': 1,
            'confirmed_data': {
                'product_name': 'Widget',
                'sku_code': 'SKU-001',
                'quantity_received': 10,
                'unit_price': 5.99,
                'supplier_name': 'Acme',
            },
        }
        response = self.client.post(self._url(), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_viewer_returns_403(self):
        self._auth(self.viewer)
        response = self.client.post(self._url(), {'scan_id': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class InvoiceScanRejectTests(APITestCase):
    """Integration tests for POST /api/ai/invoice-scan/{scan_id}/reject/"""

    @classmethod
    def setUpTestData(cls):
        cls.manager = CustomUser.objects.create_user(
            email='manager@test.com',
            username='manager@test.com',
            password='StrongPass123!',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='viewer@test.com',
            username='viewer@test.com',
            password='StrongPass123!',
            role='viewer',
        )

    def _url(self, scan_id):
        return f'/api/ai/invoice-scan/{scan_id}/reject/'

    def _auth(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_reject_success(self, mock_svc_cls):
        mock_instance = mock_svc_cls.return_value
        mock_instance.reject_scan.return_value = {
            'scan_id': 1,
            'status': 'rejected',
        }
        self._auth(self.manager)
        response = self.client.post(self._url(1))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'rejected')

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_reject_viewer_returns_403(self, mock_svc_cls):
        self._auth(self.viewer)
        response = self.client.post(self._url(1))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_reject_already_confirmed_returns_409(self, mock_svc_cls):
        from apps.ingestion.services import InvoiceAlreadyConfirmed

        mock_instance = mock_svc_cls.return_value
        mock_instance.reject_scan.side_effect = InvoiceAlreadyConfirmed('Already confirmed')
        self._auth(self.manager)
        response = self.client.post(self._url(1))
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    @patch('apps.ingestion.views.InvoiceScanService')
    def test_reject_not_found_returns_404(self, mock_svc_cls):
        from django.core.exceptions import ObjectDoesNotExist

        mock_instance = mock_svc_cls.return_value
        mock_instance.reject_scan.side_effect = ObjectDoesNotExist
        self._auth(self.manager)
        response = self.client.post(self._url(999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
