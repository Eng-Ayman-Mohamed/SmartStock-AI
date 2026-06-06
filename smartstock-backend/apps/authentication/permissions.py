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
    def has_permission(self, request, view):
        return _user_role_level(request.user) >= 1


class IsManagerOrAbove(BasePermission):
    def has_permission(self, request, view):
        return _user_role_level(request.user) >= 2


class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return _user_role_level(request.user) >= 3


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS and request.user.is_authenticated


class IsViewer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "viewer"
        )


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "manager"
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsViewerOrAbove(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ["viewer", "manager", "admin"]
        )


class IsManagerOrAbove(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ["manager", "admin"]
        )


class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
        )


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS