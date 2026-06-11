from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import CustomUser


class AuthTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            username='auth_admin', email='auth_admin@test.com', password='pass123', role='admin'
        )
        cls.manager = CustomUser.objects.create_user(
            username='auth_manager',
            email='auth_manager@test.com',
            password='pass123',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            username='auth_viewer', email='auth_viewer@test.com', password='pass123', role='viewer'
        )


class MeViewTests(AuthTestBase):
    def setUp(self):
        self.client = APIClient()

    def test_me_authenticated(self):
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['email'], 'auth_admin@test.com')

    def test_me_unauthenticated(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class LoginTests(AuthTestBase):
    def setUp(self):
        self.client = APIClient()

    def test_login_success(self):
        resp = self.client.post(
            '/api/auth/login/',
            {'username': 'auth_admin', 'password': 'pass123'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('user', resp.data)

    def test_login_wrong_password(self):
        resp = self.client.post(
            '/api/auth/login/',
            {'username': 'auth_admin', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_email(self):
        resp = self.client.post(
            '/api/auth/login/',
            {'username': 'nobody', 'password': 'pass123'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class RegisterTests(AuthTestBase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        resp = self.client.post(
            '/api/auth/register/',
            {
                'email': 'newuser@test.com',
                'name': 'New User',
                'password': 'strongpass123',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email='newuser@test.com').exists())

    def test_register_duplicate_email(self):
        resp = self.client.post(
            '/api/auth/register/',
            {
                'email': 'auth_admin@test.com',
                'name': 'Dupe User',
                'password': 'strongpass123',
            },
            format='json',
        )
        self.assertIn(resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT])


class UserManagementTests(AuthTestBase):
    def setUp(self):
        self.client = APIClient()

    def _auth(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_list_users_as_admin(self):
        self._auth(self.admin)
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_users_as_manager_fails(self):
        self._auth(self.manager)
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_as_admin(self):
        self._auth(self.admin)
        resp = self.client.post(
            '/api/auth/users/',
            {
                'email': 'created@test.com',
                'name': 'Created User',
                'password': 'strongpass123',
                'role': 'viewer',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_user_as_admin(self):
        self._auth(self.admin)
        resp = self.client.get(f'/api/auth/users/{self.viewer.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_user_role(self):
        self._auth(self.admin)
        resp = self.client.patch(
            f'/api/auth/users/{self.viewer.id}/',
            {'role': 'manager'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.viewer.refresh_from_db()
        self.assertEqual(self.viewer.role, 'manager')

    def test_retrieve_user_as_viewer_fails(self):
        self._auth(self.viewer)
        resp = self.client.get(f'/api/auth/users/{self.admin.id}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_deactivate_user(self):
        self._auth(self.admin)
        user_to_deactivate = CustomUser.objects.create_user(
            username='deactivate_me', email='deactivate@test.com', password='pass123', role='viewer'
        )
        resp = self.client.delete(f'/api/auth/users/{user_to_deactivate.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        user_to_deactivate.refresh_from_db()
        self.assertFalse(user_to_deactivate.is_active)

    def test_deactivate_already_inactive(self):
        self._auth(self.admin)
        user = CustomUser.objects.create_user(
            username='inactive_user', email='inactive@test.com', password='pass123', role='viewer'
        )
        user.is_active = False
        user.save()
        resp = self.client.delete(f'/api/auth/users/{user.id}/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class TokenRefreshTests(AuthTestBase):
    def setUp(self):
        self.client = APIClient()

    def test_refresh_with_valid_cookie(self):
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'auth_admin', 'password': 'pass123'},
            format='json',
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        refresh_token = login_resp.cookies.get('refresh_token')
        self.assertIsNotNone(refresh_token)
        self.client.cookies.load({'refresh_token': refresh_token.value})
        resp = self.client.post('/api/auth/refresh/', {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

    def test_refresh_without_cookie(self):
        resp = self.client.post('/api/auth/refresh/', {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_invalid_token(self):
        self.client.cookies.load({'refresh_token': 'invalid.token.here'})
        resp = self.client.post('/api/auth/refresh/', {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
