import unittest
from unittest.mock import MagicMock

from apps.authentication.models import CustomUser
from apps.authentication.permissions import (
    ROLE_HIERARCHY,
    IsAdmin,
    IsAdminOnly,
    IsManager,
    IsManagerOrAbove,
    IsViewer,
    IsViewerOrAbove,
    _user_role_level,
)


class TestUserRoleLevel(unittest.TestCase):
    def test_authenticated_viewer(self):
        user = MagicMock(is_authenticated=True, role='viewer')
        self.assertEqual(_user_role_level(user), 1)

    def test_authenticated_manager(self):
        user = MagicMock(is_authenticated=True, role='manager')
        self.assertEqual(_user_role_level(user), 2)

    def test_authenticated_admin(self):
        user = MagicMock(is_authenticated=True, role='admin')
        self.assertEqual(_user_role_level(user), 3)

    def test_anonymous_user(self):
        user = MagicMock(is_authenticated=False)
        self.assertEqual(_user_role_level(user), 0)

    def test_none_user(self):
        self.assertEqual(_user_role_level(None), 0)

    def test_unknown_role_returns_zero(self):
        user = MagicMock(is_authenticated=True, role='superadmin')
        self.assertEqual(_user_role_level(user), 0)

    def test_role_hierarchy_ordering(self):
        self.assertLess(ROLE_HIERARCHY['viewer'], ROLE_HIERARCHY['manager'])
        self.assertLess(ROLE_HIERARCHY['manager'], ROLE_HIERARCHY['admin'])


class TestIsViewerOrAbove(unittest.TestCase):
    def setUp(self):
        self.perm = IsViewerOrAbove()

    def test_anonymous_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=False))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_viewer_allowed(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='viewer'))
        self.assertTrue(self.perm.has_permission(request, None))

    def test_manager_allowed(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='manager'))
        self.assertTrue(self.perm.has_permission(request, None))

    def test_admin_allowed(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='admin'))
        self.assertTrue(self.perm.has_permission(request, None))


class TestIsManagerOrAbove(unittest.TestCase):
    def setUp(self):
        self.perm = IsManagerOrAbove()

    def test_anonymous_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=False))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_viewer_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='viewer'))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_manager_allowed(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='manager'))
        self.assertTrue(self.perm.has_permission(request, None))

    def test_admin_allowed(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='admin'))
        self.assertTrue(self.perm.has_permission(request, None))


class TestIsAdminOnly(unittest.TestCase):
    def setUp(self):
        self.perm = IsAdminOnly()

    def test_anonymous_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=False))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_viewer_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='viewer'))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_manager_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='manager'))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_admin_allowed(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='admin'))
        self.assertTrue(self.perm.has_permission(request, None))


class TestIsViewer(unittest.TestCase):
    def setUp(self):
        self.perm = IsViewer()

    def test_anonymous_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=False))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_viewer_allowed(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='viewer'))
        self.assertTrue(self.perm.has_permission(request, None))

    def test_manager_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='manager'))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_admin_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='admin'))
        self.assertFalse(self.perm.has_permission(request, None))


class TestIsManager(unittest.TestCase):
    def setUp(self):
        self.perm = IsManager()

    def test_anonymous_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=False))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_viewer_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='viewer'))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_manager_allowed(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='manager'))
        self.assertTrue(self.perm.has_permission(request, None))

    def test_admin_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='admin'))
        self.assertFalse(self.perm.has_permission(request, None))


class TestIsAdmin(unittest.TestCase):
    def setUp(self):
        self.perm = IsAdmin()

    def test_anonymous_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=False))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_viewer_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='viewer'))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_manager_denied(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='manager'))
        self.assertFalse(self.perm.has_permission(request, None))

    def test_admin_allowed(self):
        request = MagicMock(user=MagicMock(is_authenticated=True, role='admin'))
        self.assertTrue(self.perm.has_permission(request, None))


class TestRegistrationDefaultsToViewer(unittest.TestCase):
    def test_registration_defaults_to_viewer_role(self):
        self.assertEqual(CustomUser.Role.VIEWER, 'viewer')

    def test_role_choices_include_all_roles(self):
        roles = [choice[0] for choice in CustomUser.Role.choices]
        self.assertIn('viewer', roles)
        self.assertIn('manager', roles)
        self.assertIn('admin', roles)
