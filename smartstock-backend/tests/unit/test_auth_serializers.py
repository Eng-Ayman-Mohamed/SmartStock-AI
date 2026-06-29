from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from rest_framework.exceptions import ValidationError

from apps.authentication.serializers import (
    CookieTokenRefreshSerializer,
    CustomTokenObtainPairSerializer,
    MeSerializer,
    MeUpdateSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    RoleUpdateSerializer,
    UserCreateSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)

User = get_user_model()


class _BaseAuthSerializerTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='Testpass123!',
            first_name='John',
            last_name='Doe',
            role='manager',
        )


# ---------------------------------------------------------------------------
# _full_name helper (covered indirectly, but we test it via MeSerializer)
# ---------------------------------------------------------------------------
class FullNameHelperTest(TestCase):
    def test_full_name_with_both(self):
        from apps.authentication.serializers import _full_name
        self.assertEqual(_full_name('John', 'Doe'), 'John Doe')

    def test_full_name_first_only(self):
        from apps.authentication.serializers import _full_name
        self.assertEqual(_full_name('John', ''), 'John')

    def test_full_name_last_only(self):
        from apps.authentication.serializers import _full_name
        self.assertEqual(_full_name('', 'Doe'), 'Doe')

    def test_full_name_neither(self):
        from apps.authentication.serializers import _full_name
        self.assertEqual(_full_name('', ''), '')


# ---------------------------------------------------------------------------
# CustomTokenObtainPairSerializer
# ---------------------------------------------------------------------------
class CustomTokenObtainPairSerializerTest(_BaseAuthSerializerTest):
    def test_get_token_contains_role_and_email(self):
        token = CustomTokenObtainPairSerializer.get_token(self.user)
        self.assertEqual(token['role'], self.user.role)
        self.assertEqual(token['email'], self.user.email)

    def test_validate_with_email(self):
        data = {'email': 'test@example.com', 'password': 'Testpass123!'}
        request = self.factory.post('/')
        s = CustomTokenObtainPairSerializer(data=data, context={'request': request})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIn('access', s.validated_data)
        self.assertIn('refresh', s.validated_data)

    def test_validate_with_username(self):
        data = {'username': 'test@example.com', 'password': 'Testpass123!'}
        request = self.factory.post('/')
        s = CustomTokenObtainPairSerializer(data=data, context={'request': request})
        self.assertTrue(s.is_valid(), s.errors)

    def test_validate_no_identifier_raises(self):
        data = {'password': 'Testpass123!'}
        request = self.factory.post('/')
        s = CustomTokenObtainPairSerializer(data=data, context={'request': request})
        self.assertFalse(s.is_valid())
        self.assertIn('non_field_errors', s.errors)

    def test_validate_wrong_password(self):
        data = {'email': 'test@example.com', 'password': 'WrongPass123!'}
        request = self.factory.post('/')
        s = CustomTokenObtainPairSerializer(data=data, context={'request': request})
        self.assertFalse(s.is_valid())

    def test_validate_nonexistent_user(self):
        data = {'email': 'nobody@example.com', 'password': 'Testpass123!'}
        request = self.factory.post('/')
        s = CustomTokenObtainPairSerializer(data=data, context={'request': request})
        self.assertFalse(s.is_valid())

    def test_username_field_not_required(self):
        data = {'email': 'test@example.com', 'password': 'Testpass123!'}
        request = self.factory.post('/')
        s = CustomTokenObtainPairSerializer(data=data, context={'request': request})
        self.assertNotIn('username', [f for f in s.fields if s.fields[f].required])

    def test_email_field_is_write_only(self):
        s = CustomTokenObtainPairSerializer()
        self.assertTrue(s.fields['email'].write_only)


# ---------------------------------------------------------------------------
# CookieTokenRefreshSerializer
# ---------------------------------------------------------------------------
class CookieTokenRefreshSerializerTest(_BaseAuthSerializerTest):
    def _get_refresh_token(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        return str(RefreshToken.for_user(self.user))

    def test_validate_with_body_token(self):
        refresh = self._get_refresh_token()
        request = self.factory.post('/')
        request.COOKIES = {}
        s = CookieTokenRefreshSerializer(
            data={'refresh': refresh},
            context={'request': request},
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIn('access', s.validated_data)

    def test_validate_with_cookie_token(self):
        refresh = self._get_refresh_token()
        request = self.factory.post('/')
        request.COOKIES = {'refresh_token': refresh}
        s = CookieTokenRefreshSerializer(
            data={},
            context={'request': request},
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_validate_no_token_raises(self):
        request = self.factory.post('/')
        request.COOKIES = {}
        s = CookieTokenRefreshSerializer(
            data={},
            context={'request': request},
        )
        self.assertFalse(s.is_valid())
        self.assertIn('non_field_errors', s.errors)

    def test_validate_invalid_refresh_token(self):
        request = self.factory.post('/')
        request.COOKIES = {}
        s = CookieTokenRefreshSerializer(
            data={'refresh': 'totally-invalid-token'},
            context={'request': request},
        )
        self.assertFalse(s.is_valid())

    def test_refresh_is_write_only(self):
        s = CookieTokenRefreshSerializer()
        self.assertTrue(s.fields['refresh'].write_only)

    def test_access_is_read_only(self):
        s = CookieTokenRefreshSerializer()
        self.assertTrue(s.fields['access'].read_only)


# ---------------------------------------------------------------------------
# RegisterSerializer
# ---------------------------------------------------------------------------
class RegisterSerializerTest(TestCase):
    def test_valid_registration(self):
        data = {
            'email': 'new@example.com',
            'name': 'Jane Smith',
            'password': 'SecurePass123!',
        }
        s = RegisterSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_create_user(self):
        data = {
            'email': 'create@example.com',
            'name': 'Alice Wonder',
            'password': 'SecurePass123!',
        }
        s = RegisterSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        self.assertEqual(user.email, 'create@example.com')
        self.assertEqual(user.username, 'create@example.com')
        self.assertEqual(user.first_name, 'Alice')
        self.assertEqual(user.last_name, 'Wonder')
        self.assertEqual(user.role, 'viewer')
        self.assertTrue(user.check_password('SecurePass123!'))

    def test_create_user_single_name(self):
        data = {
            'email': 'single@example.com',
            'name': 'Cher',
            'password': 'SecurePass123!',
        }
        s = RegisterSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        self.assertEqual(user.first_name, 'Cher')
        self.assertEqual(user.last_name, '')

    def test_duplicate_email_rejected(self):
        data = {
            'email': 'test@example.com',
            'name': 'Duplicate',
            'password': 'SecurePass123!',
        }
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_duplicate_email_case_insensitive(self):
        data = {
            'email': 'TEST@EXAMPLE.COM',
            'name': 'Dup Case',
            'password': 'SecurePass123!',
        }
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_weak_password_rejected(self):
        data = {
            'email': 'weak@example.com',
            'name': 'Weak Pass',
            'password': '123',
        }
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('password', s.errors)

    def test_missing_name_rejected(self):
        data = {
            'email': 'noname@example.com',
            'password': 'SecurePass123!',
        }
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_missing_email_rejected(self):
        data = {
            'name': 'No Email',
            'password': 'SecurePass123!',
        }
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_missing_password_rejected(self):
        data = {
            'email': 'nopass@example.com',
            'name': 'No Pass',
        }
        s = RegisterSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('password', s.errors)

    def test_name_strips_whitespace(self):
        data = {
            'email': 'strip@example.com',
            'name': '  Padded  Name  ',
            'password': 'SecurePass123!',
        }
        s = RegisterSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        self.assertEqual(user.first_name, 'Padded')
        self.assertEqual(user.last_name, 'Name')

    def test_fields_present(self):
        s = RegisterSerializer()
        self.assertIn('id', s.fields)
        self.assertIn('email', s.fields)
        self.assertIn('name', s.fields)
        self.assertIn('password', s.fields)


# ---------------------------------------------------------------------------
# MeSerializer
# ---------------------------------------------------------------------------
class MeSerializerTest(_BaseAuthSerializerTest):
    def test_serializes_user(self):
        s = MeSerializer(self.user)
        data = s.data
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['name'], 'John Doe')
        self.assertEqual(data['role'], 'manager')
        self.assertIn('id', data)
        self.assertIn('is_active', data)

    def test_get_name_combines_first_last(self):
        s = MeSerializer(self.user)
        self.assertEqual(s.data['name'], 'John Doe')

    def test_get_name_with_no_last_name(self):
        self.user.last_name = ''
        self.user.save()
        s = MeSerializer(self.user)
        self.assertEqual(s.data['name'], 'John')

    def test_fields_present(self):
        s = MeSerializer()
        self.assertIn('id', s.fields)
        self.assertIn('email', s.fields)
        self.assertIn('name', s.fields)
        self.assertIn('role', s.fields)
        self.assertIn('is_active', s.fields)


# ---------------------------------------------------------------------------
# UserSerializer
# ---------------------------------------------------------------------------
class UserSerializerTest(_BaseAuthSerializerTest):
    def test_serializes_user(self):
        s = UserSerializer(self.user)
        data = s.data
        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['name'], 'John Doe')
        self.assertEqual(data['role'], 'manager')
        self.assertIn('date_joined', data)
        self.assertIn('last_login', data)

    def test_all_fields_read_only(self):
        s = UserSerializer()
        for field_name in s.Meta.read_only_fields:
            self.assertTrue(s.fields[field_name].read_only)

    def test_get_name(self):
        s = UserSerializer(self.user)
        self.assertEqual(s.data['name'], 'John Doe')

    def test_fields_complete(self):
        s = UserSerializer()
        expected = {'id', 'email', 'name', 'role', 'is_active', 'date_joined', 'last_login'}
        self.assertEqual(set(s.fields.keys()), expected)


# ---------------------------------------------------------------------------
# UserCreateSerializer
# ---------------------------------------------------------------------------
class UserCreateSerializerTest(TestCase):
    def test_valid_creation(self):
        data = {
            'email': 'admin@example.com',
            'name': 'Admin User',
            'password': 'StrongPass123!',
            'role': 'admin',
        }
        s = UserCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_create_user_with_role(self):
        data = {
            'email': 'mgr@example.com',
            'name': 'Manager Person',
            'password': 'StrongPass123!',
            'role': 'manager',
        }
        s = UserCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        self.assertEqual(user.role, 'manager')
        self.assertEqual(user.email, 'mgr@example.com')
        self.assertEqual(user.username, 'mgr@example.com')
        self.assertEqual(user.first_name, 'Manager')
        self.assertEqual(user.last_name, 'Person')

    def test_duplicate_email_rejected(self):
        User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='Testpass123!',
        )
        data = {
            'email': 'existing@example.com',
            'name': 'Dup User',
            'password': 'StrongPass123!',
            'role': 'viewer',
        }
        s = UserCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_invalid_role_rejected(self):
        data = {
            'email': 'badrole@example.com',
            'name': 'Bad Role',
            'password': 'StrongPass123!',
            'role': 'superadmin',
        }
        s = UserCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('role', s.errors)

    def test_weak_password_rejected(self):
        data = {
            'email': 'weak@example.com',
            'name': 'Weak',
            'password': '123',
            'role': 'viewer',
        }
        s = UserCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('password', s.errors)

    def test_to_representation_returns_user_serializer(self):
        data = {
            'email': 'repr@example.com',
            'name': 'Repr User',
            'password': 'StrongPass123!',
            'role': 'viewer',
        }
        s = UserCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        result = s.to_representation(user)
        self.assertIn('email', result)
        self.assertIn('name', result)
        self.assertIn('role', result)

    def test_missing_email_rejected(self):
        data = {
            'name': 'No Email',
            'password': 'StrongPass123!',
            'role': 'viewer',
        }
        s = UserCreateSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_missing_role_rejected(self):
        data = {
            'email': 'norole@example.com',
            'name': 'No Role',
            'password': 'StrongPass123!',
        }
        s = UserCreateSerializer(data=data)
        self.assertFalse(s.is_valid())


# ---------------------------------------------------------------------------
# MeUpdateSerializer
# ---------------------------------------------------------------------------
class MeUpdateSerializerTest(_BaseAuthSerializerTest):
    def test_update_name(self):
        s = MeUpdateSerializer(
            self.user,
            data={'name': 'Jane Smith'},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.first_name, 'Jane')
        self.assertEqual(updated.last_name, 'Smith')

    def test_update_email(self):
        s = MeUpdateSerializer(
            self.user,
            data={'email': 'new@example.com'},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.email, 'new@example.com')
        self.assertEqual(updated.username, 'new@example.com')

    def test_update_name_and_email(self):
        s = MeUpdateSerializer(
            self.user,
            data={'name': 'Bob New', 'email': 'bob@example.com'},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.first_name, 'Bob')
        self.assertEqual(updated.email, 'bob@example.com')

    def test_update_no_changes(self):
        s = MeUpdateSerializer(
            self.user,
            data={},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.email, self.user.email)

    def test_duplicate_email_rejected(self):
        User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='Testpass123!',
        )
        s = MeUpdateSerializer(
            self.user,
            data={'email': 'other@example.com'},
            partial=True,
        )
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_same_email_allowed(self):
        s = MeUpdateSerializer(
            self.user,
            data={'email': 'test@example.com'},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_strips_whitespace(self):
        s = MeUpdateSerializer(
            self.user,
            data={'name': '  Padded  Name  '},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.first_name, 'Padded')
        self.assertEqual(updated.last_name, 'Name')

    def test_name_single_word(self):
        s = MeUpdateSerializer(
            self.user,
            data={'name': 'Cher'},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.first_name, 'Cher')
        self.assertEqual(updated.last_name, '')

    def test_update_name_only(self):
        s = MeUpdateSerializer(
            self.user,
            data={'name': 'Only Name'},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.email, self.user.email)

    def test_update_email_only(self):
        s = MeUpdateSerializer(
            self.user,
            data={'email': 'onlyemail@example.com'},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.first_name, self.user.first_name)


# ---------------------------------------------------------------------------
# RoleUpdateSerializer
# ---------------------------------------------------------------------------
class RoleUpdateSerializerTest(_BaseAuthSerializerTest):
    def test_valid_role_update(self):
        s = RoleUpdateSerializer(self.user, data={'role': 'admin'})
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.role, 'admin')

    def test_all_valid_roles_accepted(self):
        for role in User.Role.values:
            s = RoleUpdateSerializer(self.user, data={'role': role})
            self.assertTrue(s.is_valid(), f'Role {role} should be valid')

    def test_invalid_role_rejected(self):
        s = RoleUpdateSerializer(self.user, data={'role': 'superuser'})
        self.assertFalse(s.is_valid())
        self.assertIn('role', s.errors)

    def test_missing_role_rejected(self):
        s = RoleUpdateSerializer(self.user, data={})
        self.assertFalse(s.is_valid())
        self.assertIn('role', s.errors)

    def test_empty_role_rejected(self):
        s = RoleUpdateSerializer(self.user, data={'role': ''})
        self.assertFalse(s.is_valid())


# ---------------------------------------------------------------------------
# VerifyEmailSerializer
# ---------------------------------------------------------------------------
class VerifyEmailSerializerTest(TestCase):
    def test_valid_uuid_token(self):
        import uuid
        data = {'token': str(uuid.uuid4())}
        s = VerifyEmailSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_token_format(self):
        s = VerifyEmailSerializer(data={'token': 'not-a-uuid'})
        self.assertFalse(s.is_valid())
        self.assertIn('token', s.errors)

    def test_missing_token(self):
        s = VerifyEmailSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('token', s.errors)


# ---------------------------------------------------------------------------
# ResendVerificationSerializer
# ---------------------------------------------------------------------------
class ResendVerificationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='verify@example.com',
            email='verify@example.com',
            password='Testpass123!',
            email_verified=False,
        )

    def test_valid_email(self):
        s = ResendVerificationSerializer(data={'email': 'verify@example.com'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_already_verified_rejected(self):
        self.user.email_verified = True
        self.user.save()
        s = ResendVerificationSerializer(data={'email': 'verify@example.com'})
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_nonexistent_email_accepted(self):
        s = ResendVerificationSerializer(data={'email': 'nobody@example.com'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_email_format(self):
        s = ResendVerificationSerializer(data={'email': 'not-an-email'})
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_case_insensitive_lookup(self):
        s = ResendVerificationSerializer(data={'email': 'VERIFY@EXAMPLE.COM'})
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)

    def test_missing_email(self):
        s = ResendVerificationSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('email', s.errors)
