from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.checks import Error, run_checks
from django.test import SimpleTestCase
from django.urls import resolve


class SiteStartupFunctionalTests(SimpleTestCase):
    def test_django_system_checks_pass(self):
        issues = run_checks()
        errors = [issue for issue in issues if isinstance(issue, Error)]
        self.assertEqual(errors, [], f"System checks failed: {errors}")

    def test_core_apps_are_loaded(self):
        for app_label in [
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
                self.assertIsNotNone(apps.get_app_config(app_label))

    def test_root_url_is_resolvable(self):
        match = resolve("/")
        self.assertEqual(match.route, "")

    def test_project_has_expected_top_level_structure(self):
        base_dir = Path(settings.BASE_DIR)
        expected = [
            base_dir / "manage.py",
            base_dir / "config",
            base_dir / "templates",
            base_dir / "README.md",
            base_dir / "SECURITY_NOTES.md",
        ]

        for item in expected:
            with self.subTest(item=item):
                self.assertTrue(item.exists())

    def test_templates_directory_exists(self):
        self.assertTrue((Path(settings.BASE_DIR) / "templates").exists())

    def test_email_templates_directory_exists(self):
        self.assertTrue(
            (Path(settings.BASE_DIR) / "templates" / "emails").exists()
        )

    def test_manage_py_exists(self):
        self.assertTrue((Path(settings.BASE_DIR) / "manage.py").exists())

    def test_readme_exists(self):
        self.assertTrue((Path(settings.BASE_DIR) / "README.md").exists())

    def test_security_notes_exists(self):
        self.assertTrue((Path(settings.BASE_DIR) / "SECURITY_NOTES.md").exists())

    def test_config_directory_exists(self):
        self.assertTrue((Path(settings.BASE_DIR) / "config").exists())

    def test_root_url_route_is_empty_pattern(self):
        match = resolve("/")
        self.assertEqual(match.route, "")

    def test_admin_url_is_resolvable(self):
        match = resolve("/admin/")
        self.assertEqual(match.app_name, "admin")

    def test_swagger_url_is_resolvable(self):
        match = resolve("/swagger/")
        self.assertEqual(match.route, "swagger/")

    def test_redoc_url_is_resolvable(self):
        match = resolve("/redoc/")
        self.assertEqual(match.route, "redoc/")

    def test_apps_registry_contains_biens(self):
        self.assertIsNotNone(apps.get_app_config("biens"))

    def test_apps_registry_contains_utilisateurs(self):
        self.assertIsNotNone(apps.get_app_config("utilisateurs"))

    def test_apps_registry_contains_reservations(self):
        self.assertIsNotNone(apps.get_app_config("reservations"))
