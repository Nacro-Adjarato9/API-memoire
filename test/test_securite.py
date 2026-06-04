from django.conf import settings
from django.test import SimpleTestCase


class ProjectSecurityTests(SimpleTestCase):
    def test_secret_key_is_not_empty(self):
        self.assertTrue(settings.SECRET_KEY)
        self.assertNotEqual(settings.SECRET_KEY, "django-insecure-change-me")

    def test_debug_mode_is_boolean(self):
        self.assertIsInstance(settings.DEBUG, bool)

    def test_login_redirects_are_defined(self):
        self.assertTrue(settings.LOGIN_REDIRECT_URL.startswith("/"))
        self.assertTrue(settings.LOGOUT_REDIRECT_URL.startswith("/"))

    def test_allowed_hosts_include_local_domains(self):
        self.assertIn("localhost", settings.ALLOWED_HOSTS)
        self.assertIn("127.0.0.1", settings.ALLOWED_HOSTS)
        self.assertIn("testserver", settings.ALLOWED_HOSTS)

    def test_security_middleware_is_enabled(self):
        self.assertIn(
            "django.middleware.security.SecurityMiddleware",
            settings.MIDDLEWARE,
        )

    def test_csrf_middleware_is_enabled(self):
        self.assertIn(
            "django.middleware.csrf.CsrfViewMiddleware",
            settings.MIDDLEWARE,
        )

    def test_session_middleware_is_enabled(self):
        self.assertIn(
            "django.contrib.sessions.middleware.SessionMiddleware",
            settings.MIDDLEWARE,
        )

    def test_clickjacking_middleware_is_enabled(self):
        self.assertIn(
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            settings.MIDDLEWARE,
        )

    def test_cors_middleware_is_enabled(self):
        self.assertIn("corsheaders.middleware.CorsMiddleware", settings.MIDDLEWARE)

    def test_email_backend_is_set(self):
        self.assertIn(
            settings.EMAIL_BACKEND,
            [
                "django.core.mail.backends.console.EmailBackend",
                "django.core.mail.backends.locmem.EmailBackend",
            ],
        )

    def test_default_from_email_is_defined(self):
        self.assertTrue(settings.DEFAULT_FROM_EMAIL)

    def test_server_email_is_defined(self):
        self.assertTrue(settings.SERVER_EMAIL)

    def test_cors_origins_are_defined(self):
        self.assertGreaterEqual(len(settings.CORS_ALLOWED_ORIGINS), 4)

    def test_password_validators_are_configured(self):
        self.assertGreaterEqual(len(settings.AUTH_PASSWORD_VALIDATORS), 4)
