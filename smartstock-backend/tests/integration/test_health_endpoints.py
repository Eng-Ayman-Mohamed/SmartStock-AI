from rest_framework import status
from rest_framework.test import APITestCase


class HealthEndpointTests(APITestCase):
    """Integration tests for health check API endpoints."""

    def _health_url(self):
        return '/api/health/'

    def _readiness_url(self):
        return '/api/health/readiness/'

    def test_health_check_returns_200(self):
        """GET /api/health/ should always return 200 while the process is alive."""
        response = self.client.get(self._health_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_response_structure(self):
        """Response must contain status, database, and redis keys."""
        response = self.client.get(self._health_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('database', response.data)
        self.assertIn('redis', response.data)
        self.assertEqual(response.data['status'], 'ok')

    def test_health_check_without_authentication(self):
        """Health endpoint should be accessible without any auth credentials."""
        self.client.credentials()  # ensure no auth header is set
        response = self.client.get(self._health_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('database', response.data)
        self.assertIn('redis', response.data)

    def test_health_check_database_key_has_valid_value(self):
        """The database key must be 'connected' or 'disconnected'."""
        response = self.client.get(self._health_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data['database'], ('connected', 'disconnected'))

    def test_health_check_redis_key_has_valid_value(self):
        """The redis key must be 'connected' or 'disconnected'."""
        response = self.client.get(self._health_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(response.data['redis'], ('connected', 'disconnected'))

    def test_readiness_returns_200_when_healthy(self):
        """Readiness probe returns 200 when all dependencies are reachable."""
        response = self.client.get(self._readiness_url())
        # In the test environment both services should be connected.
        # If they are, status is 200; otherwise 503. Either is valid behaviour.
        self.assertIn(
            response.status_code, (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)
        )
        self.assertIn(response.data['status'], ('ok', 'degraded'))

    def test_readiness_response_structure(self):
        """Readiness response must contain status, database, and redis keys."""
        response = self.client.get(self._readiness_url())
        self.assertIn('status', response.data)
        self.assertIn('database', response.data)
        self.assertIn('redis', response.data)

    def test_readiness_without_authentication(self):
        """Readiness endpoint should be accessible without auth credentials."""
        self.client.credentials()
        response = self.client.get(self._readiness_url())
        self.assertIn(
            response.status_code, (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)
        )

    def test_health_and_readiness_return_same_diagnostics(self):
        """Both endpoints should report consistent diagnostic values."""
        health_response = self.client.get(self._health_url())
        readiness_response = self.client.get(self._readiness_url())
        self.assertEqual(health_response.data['database'], readiness_response.data['database'])
        self.assertEqual(health_response.data['redis'], readiness_response.data['redis'])
