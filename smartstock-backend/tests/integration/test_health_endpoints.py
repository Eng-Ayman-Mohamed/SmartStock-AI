import os
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase


class LivenessEndpointTests(APITestCase):
    """Integration tests for the liveness probe."""

    def _url(self):
        return '/api/health/live/'

    def test_returns_200(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_structure_minimal(self):
        """Liveness must NOT expose dependency information."""
        response = self.client.get(self._url())
        self.assertEqual(response.data, {'status': 'ok'})
        self.assertNotIn('database', response.data)
        self.assertNotIn('redis', response.data)

    def test_no_auth_required(self):
        self.client.credentials()
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ReadinessEndpointTests(APITestCase):
    """Integration tests for the readiness probe."""

    def _url(self):
        return '/api/health/ready/'

    def _get_as_external(self, **kwargs):
        """Make request as if from an external (public) IP."""
        return self.client.get(
            self._url(),
            REMOTE_ADDR='203.0.113.1',
            **kwargs,
        )

    def test_forbidden_without_secret_and_external_ip(self):
        """External request without secret header must be rejected."""
        self.client.credentials()
        response = self._get_as_external()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['status'], 'forbidden')

    def test_allowed_with_valid_secret(self):
        """Request with correct X-Health-Secret header is accepted."""
        with patch.dict(os.environ, {'HEALTH_SECRET_HEADER': 'test-secret-123'}):
            response = self.client.get(
                self._url(),
                HTTP_X_HEALTH_SECRET='test-secret-123',
                REMOTE_ADDR='203.0.113.1',
            )
            self.assertIn(
                response.status_code,
                (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE),
            )

    def test_forbidden_with_wrong_secret(self):
        """Request with wrong secret header is rejected."""
        with patch.dict(os.environ, {'HEALTH_SECRET_HEADER': 'test-secret-123'}):
            response = self._get_as_external(HTTP_X_HEALTH_SECRET='wrong-secret')
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_allowed_from_internal_network(self):
        """Requests from internal networks (127.0.0.1) are allowed without secret."""
        response = self.client.get(self._url())
        # In test env, REMOTE_ADDR is 127.0.0.1 (internal)
        self.assertIn(
            response.status_code,
            (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE),
        )

    def test_response_structure_no_details(self):
        """Readiness must NOT expose database/redis status externally."""
        self.client.credentials()
        response = self._get_as_external()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('database', response.data)
        self.assertNotIn('redis', response.data)

    def test_readiness_shows_status_only(self):
        """When allowed (internal), response contains only status field."""
        response = self.client.get(self._url())
        self.assertIn('status', response.data)
        self.assertNotIn('database', response.data)
        self.assertNotIn('redis', response.data)
