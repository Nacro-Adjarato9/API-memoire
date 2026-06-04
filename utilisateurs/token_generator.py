from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from datetime import timedelta
import secrets
from utilisateurs.models import UserProfile


class EmailVerificationTokenGenerator:
    """Generate and validate email verification tokens"""

    @staticmethod
    def generate_token(user):
        """Generate a token for email verification (valid for 24 hours)"""
        token = secrets.token_urlsafe(32)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.verification_token = token
        profile.verification_token_expires = timezone.now() + timedelta(hours=24)
        profile.save()
        return token

    @staticmethod
    def verify_token(user, token):
        """Verify if token is valid and not expired"""
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return False

        if profile.verification_token != token:
            return False

        if profile.verification_token_expires < timezone.now():
            return False

        return True

    @staticmethod
    def mark_as_verified(user):
        """Mark user email as verified"""
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_verified = True
        profile.verification_token = None
        profile.verification_token_expires = None
        profile.save()
