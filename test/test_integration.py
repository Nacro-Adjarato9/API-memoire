from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class TemplateAndAdminIntegrationTests(TestCase):
    def test_email_templates_render(self):
        user = User(username="demo", first_name="Demo")

        verify_html = render_to_string(
            "emails/verify_email.html",
            {
                "user": user,
                "verification_link": "http://example.com/verify",
                "expiry_hours": 24,
            },
        )
        reset_html = render_to_string(
            "emails/reset_password.html",
            {
                "user": user,
                "reset_link": "http://example.com/reset",
                "expiry_hours": 24,
            },
        )

        self.assertIn("Vérification d'Email", verify_html)
        self.assertIn("Réinitialisation", reset_html)

    def test_admin_entry_point_is_reachable(self):
        client = Client()
        response = client.get("/admin/")
        self.assertIn(response.status_code, [200, 302])
        self.assertEqual(reverse("admin:index"), "/admin/")

    def test_verify_email_template_contains_verification_link(self):
        user = User(username="demo", first_name="Demo")
        html = render_to_string(
            "emails/verify_email.html",
            {
                "user": user,
                "verification_link": "http://example.com/verify",
                "expiry_hours": 24,
            },
        )
        self.assertIn("http://example.com/verify", html)

    def test_reset_password_template_contains_reset_link(self):
        user = User(username="demo", first_name="Demo")
        html = render_to_string(
            "emails/reset_password.html",
            {
                "user": user,
                "reset_link": "http://example.com/reset",
                "expiry_hours": 24,
            },
        )
        self.assertIn("http://example.com/reset", html)

    def test_verify_email_template_mentions_expiry_hours(self):
        user = User(username="demo", first_name="Demo")
        html = render_to_string(
            "emails/verify_email.html",
            {
                "user": user,
                "verification_link": "http://example.com/verify",
                "expiry_hours": 24,
            },
        )
        self.assertIn("24 heures", html)

    def test_reset_password_template_mentions_expiry_hours(self):
        user = User(username="demo", first_name="Demo")
        html = render_to_string(
            "emails/reset_password.html",
            {
                "user": user,
                "reset_link": "http://example.com/reset",
                "expiry_hours": 24,
            },
        )
        self.assertIn("24 heures", html)

    def test_admin_login_page_is_reachable(self):
        client = Client()
        response = client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in")

    def test_swagger_page_is_reachable(self):
        client = Client()
        response = client.get("/swagger/")
        self.assertIn(response.status_code, [200, 302])

    def test_redoc_page_is_reachable(self):
        client = Client()
        response = client.get("/redoc/")
        self.assertIn(response.status_code, [200, 302])

    def test_admin_index_url_reverses(self):
        self.assertEqual(reverse("admin:index"), "/admin/")

    def test_admin_login_url_reverses(self):
        self.assertEqual(reverse("admin:login"), "/admin/login/")
