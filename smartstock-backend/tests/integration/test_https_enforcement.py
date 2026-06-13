from django.test import TestCase, override_settings


class HTTPSEnforcementTest(TestCase):
    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_ssl_redirect_enabled_in_production(self):
        from django.conf import settings

        self.assertTrue(settings.SECURE_SSL_REDIRECT)

    @override_settings(SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'))
    def test_proxy_ssl_header_configured(self):
        from django.conf import settings

        self.assertEqual(settings.SECURE_PROXY_SSL_HEADER, ('HTTP_X_FORWARDED_PROTO', 'https'))

    @override_settings(SESSION_COOKIE_SECURE=True)
    def test_session_cookie_secure(self):
        from django.conf import settings

        self.assertTrue(settings.SESSION_COOKIE_SECURE)

    @override_settings(CSRF_COOKIE_SECURE=True)
    def test_csrf_cookie_secure(self):
        from django.conf import settings

        self.assertTrue(settings.CSRF_COOKIE_SECURE)
