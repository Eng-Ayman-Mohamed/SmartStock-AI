from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import CustomUser


class AuthEndpointTests(APITestCase):
    """Integration tests for authentication API endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            email='test@example.com',
            username='test@example.com',
            password='StrongPass123!',
            role='viewer',
        )

    def _login_url(self):
        return '/api/auth/login/'

    def _register_url(self):
        return '/api/auth/register/'

    def _refresh_url(self):
        return '/api/auth/refresh/'

    def _logout_url(self):
        return '/api/auth/logout/'

    def _me_url(self):
        return '/api/auth/me/'

    def test_login_valid_credentials(self):
        response = self.client.post(
            self._login_url(),
            {'email': 'test@example.com', 'password': 'StrongPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)
        self.assertIn('refresh_token', response.cookies)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            self._login_url(),
            {'email': 'test@example.com', 'password': 'wrongpassword'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_with_cookie(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['refresh_token'] = str(refresh)
        response = self.client.post(self._refresh_url(), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_without_cookie(self):
        response = self.client.post(self._refresh_url(), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['refresh_token'] = str(refresh)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.post(self._logout_url(), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_protected_endpoint_with_token(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.get(self._me_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_protected_endpoint_without_token(self):
        response = self.client.get(self._me_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_duplicate_email_returns_409(self):
        response = self.client.post(
            self._register_url(),
            {
                'email': 'test@example.com',
                'name': 'Another User',
                'password': 'StrongPass456!',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_register_password_validation(self):
        response = self.client.post(
            self._register_url(),
            {
                'email': 'weak@example.com',
                'name': 'Weak User',
                'password': 'short',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
