"""Tests for audit/utils.py edge cases and audit/middleware edge cases."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from apps.audit.middleware import AuditMiddleware, _get_client_ip
from apps.audit.models import AuditLog
from apps.audit.utils import log_ai_action

User = get_user_model()


class LogAiActionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='audit@test.com', email='audit@test.com', password='testpass123'
        )

    def test_log_ai_action_success(self):
        log_ai_action(
            event='AI_NL_QUERY',
            user=self.user,
            entity_type='Product',
            entity_id=1,
            data={'query': 'test'},
            ip='127.0.0.1',
        )
        log = AuditLog.objects.latest('id')
        self.assertEqual(log.event, 'AI_NL_QUERY')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.entity_type, 'Product')
        self.assertEqual(log.entity_id, 1)
        self.assertEqual(log.data_snapshot, {'query': 'test'})
        self.assertEqual(log.ip_address, '127.0.0.1')

    def test_log_ai_action_exception_does_not_propagate(self):
        with patch.object(AuditLog.objects, 'create', side_effect=Exception('db fail')):
            log_ai_action(event='AI_RAG_QUERY', user=self.user)


class GetClientIpTest(TestCase):
    def test_x_forwarded_for(self):
        request = MagicMock()
        request.META = {'HTTP_X_FORWARDED_FOR': '1.2.3.4, 5.6.7.8'}
        self.assertEqual(_get_client_ip(request), '1.2.3.4')

    def test_remote_addr_fallback(self):
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '10.0.0.1'}
        self.assertEqual(_get_client_ip(request), '10.0.0.1')

    def test_no_ip(self):
        request = MagicMock()
        request.META = {}
        self.assertIsNone(_get_client_ip(request))


class AuditMiddlewareEdgeCasesTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuditMiddleware(get_response=lambda r: MagicMock(status_code=200))

    def test_non_login_path_ignored(self):
        request = self.factory.post('/api/products/', content_type='application/json')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        response = MagicMock(status_code=200)
        before = AuditLog.objects.filter(event='USER_LOGIN').count()
        self.middleware.process_response(request, response)
        self.assertEqual(AuditLog.objects.filter(event='USER_LOGIN').count(), before)

    def test_get_login_ignored(self):
        request = self.factory.get('/api/auth/login/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        response = MagicMock(status_code=200)
        before = AuditLog.objects.filter(event='USER_LOGIN').count()
        self.middleware.process_response(request, response)
        self.assertEqual(AuditLog.objects.filter(event='USER_LOGIN').count(), before)

    def test_non_200_response_ignored(self):
        request = self.factory.post(
            '/api/auth/login/',
            content_type='application/json',
        )
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        response = MagicMock(status_code=401, content=b'{"error":"bad"}')
        before = AuditLog.objects.filter(event='USER_LOGIN').count()
        self.middleware.process_response(request, response)
        self.assertEqual(AuditLog.objects.filter(event='USER_LOGIN').count(), before)

    def test_json_decode_error_sets_user_id_none(self):
        request = self.factory.post(
            '/api/auth/login/',
            content_type='application/json',
        )
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        response = MagicMock(status_code=200, content=b'not json')
        before = AuditLog.objects.filter(event='USER_LOGIN').count()
        self.middleware.process_response(request, response)
        self.assertEqual(AuditLog.objects.filter(event='USER_LOGIN').count(), before + 1)
        log = AuditLog.objects.filter(event='USER_LOGIN').latest('id')
        self.assertIsNone(log.entity_id)

    def test_x_forwarded_for_in_login(self):
        request = self.factory.post(
            '/api/auth/login/',
            content_type='application/json',
        )
        request.META['HTTP_X_FORWARDED_FOR'] = '1.2.3.4, 5.6.7.8'
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        response = MagicMock(
            status_code=200,
            content=b'{"user": {"id": 1}}',
        )
        self.middleware.process_response(request, response)
        log = AuditLog.objects.filter(event='USER_LOGIN').latest('id')
        self.assertEqual(log.ip_address, '1.2.3.4')
