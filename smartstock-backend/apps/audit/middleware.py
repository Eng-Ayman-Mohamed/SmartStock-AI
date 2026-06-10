import json
import logging

from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    """Extract real IP, respecting reverse proxy X-Forwarded-For."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class AuditMiddleware(MiddlewareMixin):
    """
    Logs USER_LOGIN events by watching POST /api/auth/login/.
    The response phase is used (not request) so we only log successful logins
    by checking response status 200.
    """

    LOGIN_PATH = '/api/auth/login/'

    def process_response(self, request, response):
        if request.path == self.LOGIN_PATH and request.method == 'POST':
            if response.status_code == 200:
                # Parse user identity from the response body
                try:
                    body = json.loads(response.content)
                    user_id = body.get('user', {}).get('id')
                except (json.JSONDecodeError, AttributeError):
                    user_id = None

                try:
                    AuditLog.objects.create(
                        event='USER_LOGIN',
                        entity_type='User',
                        entity_id=user_id,
                        ip_address=_get_client_ip(request),
                        data_snapshot={'path': request.path, 'method': request.method},
                    )
                except Exception as e:
                    logger.exception("Failed to log login audit entry: %s", e)
        return response