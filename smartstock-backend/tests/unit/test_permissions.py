from unittest.mock import MagicMock

from django.test import RequestFactory

from apps.authentication.permissions import (
    IsAdmin,
    IsAdminOnly,
    IsManager,
    IsManagerOrAbove,
    IsViewer,
    IsViewerOrAbove,
    ReadOnly,
)


def _request(method='GET', user=None):
    factory = RequestFactory()
    req = factory.generic(method, '/')
    req.user = user
    return req


def _mock_user(role=None):
    user = MagicMock()
    user.is_authenticated = bool(role)
    user.role = role
    return user


class TestIsViewerOrAbove:
    def test_anon_denied(self):
        assert not IsViewerOrAbove().has_permission(_request(user=_mock_user(None)), None)

    def test_viewer_allowed(self):
        assert IsViewerOrAbove().has_permission(_request(user=_mock_user('viewer')), None)

    def test_manager_allowed(self):
        assert IsViewerOrAbove().has_permission(_request(user=_mock_user('manager')), None)

    def test_admin_allowed(self):
        assert IsViewerOrAbove().has_permission(_request(user=_mock_user('admin')), None)


class TestIsManagerOrAbove:
    def test_anon_denied(self):
        assert not IsManagerOrAbove().has_permission(_request(user=_mock_user(None)), None)

    def test_viewer_denied(self):
        assert not IsManagerOrAbove().has_permission(_request(user=_mock_user('viewer')), None)

    def test_manager_allowed(self):
        assert IsManagerOrAbove().has_permission(_request(user=_mock_user('manager')), None)

    def test_admin_allowed(self):
        assert IsManagerOrAbove().has_permission(_request(user=_mock_user('admin')), None)


class TestIsAdminOnly:
    def test_anon_denied(self):
        assert not IsAdminOnly().has_permission(_request(user=_mock_user(None)), None)

    def test_viewer_denied(self):
        assert not IsAdminOnly().has_permission(_request(user=_mock_user('viewer')), None)

    def test_manager_denied(self):
        assert not IsAdminOnly().has_permission(_request(user=_mock_user('manager')), None)

    def test_admin_allowed(self):
        assert IsAdminOnly().has_permission(_request(user=_mock_user('admin')), None)


class TestReadOnly:
    def test_anon_denied_safe(self):
        assert not ReadOnly().has_permission(_request(method='GET', user=_mock_user(None)), None)

    def test_anon_denied_unsafe(self):
        assert not ReadOnly().has_permission(_request(method='POST', user=_mock_user(None)), None)

    def test_viewer_allowed_safe(self):
        assert ReadOnly().has_permission(_request(method='GET', user=_mock_user('viewer')), None)

    def test_viewer_denied_unsafe(self):
        assert not ReadOnly().has_permission(
            _request(method='POST', user=_mock_user('viewer')), None
        )

    def test_manager_allowed_safe(self):
        assert ReadOnly().has_permission(_request(method='GET', user=_mock_user('manager')), None)

    def test_manager_allowed_unsafe(self):
        assert ReadOnly().has_permission(_request(method='POST', user=_mock_user('manager')), None)


class TestIsViewer:
    def test_anon_denied(self):
        assert not IsViewer().has_permission(_request(user=_mock_user(None)), None)

    def test_viewer_allowed(self):
        assert IsViewer().has_permission(_request(user=_mock_user('viewer')), None)

    def test_manager_denied(self):
        assert not IsViewer().has_permission(_request(user=_mock_user('manager')), None)

    def test_admin_denied(self):
        assert not IsViewer().has_permission(_request(user=_mock_user('admin')), None)


class TestIsManager:
    def test_anon_denied(self):
        assert not IsManager().has_permission(_request(user=_mock_user(None)), None)

    def test_viewer_denied(self):
        assert not IsManager().has_permission(_request(user=_mock_user('viewer')), None)

    def test_manager_allowed(self):
        assert IsManager().has_permission(_request(user=_mock_user('manager')), None)

    def test_admin_denied(self):
        assert not IsManager().has_permission(_request(user=_mock_user('admin')), None)


class TestIsAdmin:
    def test_anon_denied(self):
        assert not IsAdmin().has_permission(_request(user=_mock_user(None)), None)

    def test_viewer_denied(self):
        assert not IsAdmin().has_permission(_request(user=_mock_user('viewer')), None)

    def test_manager_denied(self):
        assert not IsAdmin().has_permission(_request(user=_mock_user('manager')), None)

    def test_admin_allowed(self):
        assert IsAdmin().has_permission(_request(user=_mock_user('admin')), None)
