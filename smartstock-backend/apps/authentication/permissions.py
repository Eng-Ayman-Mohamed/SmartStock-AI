from rest_framework.permissions import BasePermission, SAFE_METHODS


ROLE_HIERARCHY = {
    'admin': 3,
    'manager': 2,
    'viewer': 1,
}


def _user_role_level(user):
    if not user or not user.is_authenticated:
        return 0
    return ROLE_HIERARCHY.get(user.role, 0)


class IsViewerOrAbove(BasePermission):
    message = 'Viewer role or above required.'

    def has_permission(self, request, view):
        level = _user_role_level(request.user)
        return level >= 1


class IsManagerOrAbove(BasePermission):
    message = 'Manager role or above required.'

    def has_permission(self, request, view):
        level = _user_role_level(request.user)
        return level >= 2


class IsAdminOnly(BasePermission):
    message = 'Admin role required.'

    def has_permission(self, request, view):
        level = _user_role_level(request.user)
        return level >= 3


class ReadOnly(BasePermission):
    message = 'Write operations require Manager role or above.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return _user_role_level(request.user) >= 1
        return _user_role_level(request.user) >= 2


class IsViewer(BasePermission):
    message = 'Viewer role required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'viewer'
        )


class IsManager(BasePermission):
    message = 'Manager role required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'manager'
        )


class IsAdmin(BasePermission):
    message = 'Admin role required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'admin'
        )
