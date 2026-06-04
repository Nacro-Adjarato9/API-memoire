from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from utilisateurs.emails import (
    send_password_reset_email,
    send_verification_email,
)
from utilisateurs.models import UserProfile
from utilisateurs.token_generator import EmailVerificationTokenGenerator


User = get_user_model()


class TokenGeneratorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tokenuser",
            email="token@example.com",
            password="StrongPass123!",
        )

    def test_generate_token_creates_profile_token(self):
        token = EmailVerificationTokenGenerator.generate_token(self.user)
        profile = UserProfile.objects.get(user=self.user)

        self.assertTrue(token)
        self.assertEqual(profile.verification_token, token)
        self.assertIsNotNone(profile.verification_token_expires)

    def test_verify_token_returns_true_for_valid_token(self):
        profile = self.user.profile
        profile.verification_token = "valid-token"
        profile.verification_token_expires = timezone.now() + timedelta(hours=1)
        profile.save()

        self.assertTrue(
            EmailVerificationTokenGenerator.verify_token(self.user, "valid-token")
        )

    def test_verify_token_returns_false_for_invalid_token(self):
        EmailVerificationTokenGenerator.generate_token(self.user)
        self.assertFalse(
            EmailVerificationTokenGenerator.verify_token(self.user, "wrong-token")
        )

    def test_verify_token_returns_false_for_expired_token(self):
        profile = self.user.profile
        profile.verification_token = "expired-token"
        profile.verification_token_expires = timezone.now() - timedelta(hours=1)
        profile.save()

        self.assertFalse(
            EmailVerificationTokenGenerator.verify_token(self.user, "expired-token")
        )

    def test_mark_as_verified_clears_token_and_sets_flag(self):
        token = EmailVerificationTokenGenerator.generate_token(self.user)
        EmailVerificationTokenGenerator.mark_as_verified(self.user)
        profile = UserProfile.objects.get(user=self.user)

        self.assertTrue(profile.is_verified)
        self.assertIsNone(profile.verification_token)
        self.assertIsNone(profile.verification_token_expires)
        self.assertNotEqual(profile.verification_token, token)


class EmailHelperTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mailuser",
            email="mail@example.com",
            password="StrongPass123!",
        )

    @patch("utilisateurs.emails.send_mail")
    def test_send_verification_email_calls_send_mail(self, mocked_send_mail):
        send_verification_email(self.user, "abc123")

        mocked_send_mail.assert_called_once()
        args, kwargs = mocked_send_mail.call_args
        self.assertIn("V", args[0])
        self.assertIn("verify-email", args[1])
        self.assertIn("html_message", kwargs)

    @patch("utilisateurs.emails.send_mail")
    def test_send_password_reset_email_calls_send_mail(self, mocked_send_mail):
        send_password_reset_email(self.user, "abc123")

        mocked_send_mail.assert_called_once()
        args, kwargs = mocked_send_mail.call_args
        self.assertIn("R", args[0])
        self.assertIn("reset-password", args[1])
        self.assertIn("html_message", kwargs)

    @patch("utilisateurs.emails.send_mail")
    def test_send_verification_email_uses_frontend_url(self, mocked_send_mail):
        send_verification_email(self.user, "token-1")
        args, _ = mocked_send_mail.call_args
        self.assertIn("http://localhost:3000", args[1])

    @patch("utilisateurs.emails.send_mail")
    def test_send_password_reset_email_uses_frontend_url(self, mocked_send_mail):
        send_password_reset_email(self.user, "token-2")
        args, _ = mocked_send_mail.call_args
        self.assertIn("http://localhost:3000", args[1])
