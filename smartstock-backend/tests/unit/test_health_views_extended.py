"""Tests for apps/health/views.py — readiness edge cases."""

from rest_framework.test import APITestCase


class ReadinessEdgeCaseTests(APITestCase):
    def _url(self):
        return '/api/health/ready/'

    def test_internal_ip_allowed_without_secret(self):
        response = self.client.get(self._url(), REMOTE_ADDR='192.168.1.1')
        self.assertIn(response.status_code, (200, 503))

    def test_xff_internal_ip_allowed(self):
        response = self.client.get(
            self._url(),
            REMOTE_ADDR='203.0.113.1',
            HTTP_X_FORWARDED_FOR='10.0.0.5, 203.0.113.1',
        )
        self.assertIn(response.status_code, (200, 503))

    def test_xff_invalid_ip_forbidden(self):
        response = self.client.get(
            self._url(),
            REMOTE_ADDR='203.0.113.1',
            HTTP_X_FORWARDED_FOR='not-an-ip',
        )
        self.assertEqual(response.status_code, 403)

    def test_empty_xff_and_public_ip_forbidden(self):
        response = self.client.get(
            self._url(),
            REMOTE_ADDR='8.8.8.8',
            HTTP_X_FORWARDED_FOR='',
        )
        self.assertEqual(response.status_code, 403)

    def test_secret_wrong_with_no_env_secret_forbidden(self):
        response = self.client.get(
            self._url(),
            REMOTE_ADDR='203.0.113.1',
            HTTP_X_HEALTH_SECRET='some-secret',
        )
        self.assertEqual(response.status_code, 403)

    def test_127_0_0_1_is_internal(self):
        response = self.client.get(self._url(), REMOTE_ADDR='127.0.0.1')
        self.assertIn(response.status_code, (200, 503))

    def test_172_16_is_internal(self):
        response = self.client.get(self._url(), REMOTE_ADDR='172.16.0.1')
        self.assertIn(response.status_code, (200, 503))
