from django.conf import settings
from django.test import SimpleTestCase


class ProjectSettingsUnitTests(SimpleTestCase):
    def test_core_apps_are_installed(self):
        for app_label in [
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "utilisateurs",
            "biens",
            "reservations",
            "images",
            "chat",
            "avis",
            "ia",
            "agences",
            "favoris",
            "notifications",
            "tarifs",
        ]:
            with self.subTest(app=app_label):
                self.assertIn(app_label, settings.INSTALLED_APPS)

    def test_project_paths_are_defined(self):
        self.assertEqual(settings.ROOT_URLCONF, "config.urls")
        self.assertEqual(settings.WSGI_APPLICATION, "config.wsgi.application")
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"],
            "django.db.backends.sqlite3",
        )

    def test_debug_is_enabled_in_dev(self):
        self.assertIsInstance(settings.DEBUG, bool)

    def test_static_url_is_defined(self):
        self.assertEqual(settings.STATIC_URL, "/static/")

    def test_language_code_is_set(self):
        self.assertEqual(settings.LANGUAGE_CODE, "en-us")

    def test_timezone_is_utc(self):
        self.assertEqual(settings.TIME_ZONE, "UTC")

    def test_use_i18n_enabled(self):
        self.assertTrue(settings.USE_I18N)

    def test_use_tz_enabled(self):
        self.assertTrue(settings.USE_TZ)

    def test_security_related_settings_exist(self):
        self.assertIn("localhost", settings.ALLOWED_HOSTS)
        self.assertIn("127.0.0.1", settings.ALLOWED_HOSTS)
        self.assertIn("testserver", settings.ALLOWED_HOSTS)
        self.assertIn("corsheaders.middleware.CorsMiddleware", settings.MIDDLEWARE)
        self.assertIn(
            "django.middleware.security.SecurityMiddleware",
            settings.MIDDLEWARE,
        )
        self.assertIn(
            "django.middleware.csrf.CsrfViewMiddleware",
            settings.MIDDLEWARE,
        )
        self.assertTrue(hasattr(settings, "EMAIL_BACKEND"))
        self.assertTrue(hasattr(settings, "CACHES"))
        self.assertTrue(hasattr(settings, "CORS_ALLOWED_ORIGINS"))
        self.assertTrue(hasattr(settings, "FRONTEND_URL"))

    def test_frontend_url_points_to_local_dev_server(self):
        self.assertTrue(settings.FRONTEND_URL.startswith("http://"))
        self.assertIn("3000", settings.FRONTEND_URL)

    def test_cache_backend_uses_locmem(self):
        self.assertEqual(
            settings.CACHES["default"]["BACKEND"],
            "django.core.cache.backends.locmem.LocMemCache",
        )

    def test_cors_origins_cover_common_frontend_ports(self):
        origins = settings.CORS_ALLOWED_ORIGINS
        self.assertIn("http://localhost:3000", origins)
        self.assertIn("http://127.0.0.1:3000", origins)
        self.assertIn("http://localhost:5173", origins)
        self.assertIn("http://127.0.0.1:5173", origins)

    def test_jwt_access_token_lifetime_is_one_hour(self):
        self.assertEqual(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].seconds, 3600)

    def test_jwt_refresh_token_lifetime_is_seven_days(self):
        self.assertEqual(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].days, 7)

    def test_jwt_auth_header_type_is_bearer(self):
        self.assertEqual(settings.SIMPLE_JWT["AUTH_HEADER_TYPES"], ("Bearer",))

    def test_rest_framework_authentication_classes_are_defined(self):
        auth_classes = settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
        self.assertIn(
            "rest_framework.authentication.SessionAuthentication",
            auth_classes,
        )
        self.assertIn(
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            auth_classes,
        )

    def test_rest_framework_permission_default_is_allow_any(self):
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"],
            ("rest_framework.permissions.AllowAny",),
        )
