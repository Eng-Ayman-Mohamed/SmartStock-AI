from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class SAFEAnonRateThrottle(AnonRateThrottle):
    def allow_request(self, request, view):
        if request.method == 'OPTIONS':
            return True
        return super().allow_request(request, view)


class SAFEUserRateThrottle(UserRateThrottle):
    def allow_request(self, request, view):
        if request.method == 'OPTIONS':
            return True
        return super().allow_request(request, view)


class AIRateThrottle(UserRateThrottle):
    scope = 'ai'

    def allow_request(self, request, view):
        if request.method == 'OPTIONS':
            return True
        return super().allow_request(request, view)
