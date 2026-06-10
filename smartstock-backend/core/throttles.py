from rest_framework.throttling import UserRateThrottle


class AIRateThrottle(UserRateThrottle):
    scope = 'ai'
