class OPTIONSThrottleExemptionMixin:
    def check_throttles(self, request):
        if request.method == 'OPTIONS':
            return
        return super().check_throttles(request)
