from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_verification_email(user, token):
    """Send verification email to user with a 6-digit code to type manually
    (web and mobile use the same code, no dependency on a clickable link/URL)."""
    context = {
        'user': user,
        'code': token,
        'expiry_hours': 24,
    }

    subject = "Votre code de vérification"
    html_message = render_to_string('emails/verify_email.html', context)
    plain_message = f"Votre code de vérification LogCiv : {token}\n\nCe code expire dans 24 heures."
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, token):
    """Send password reset email"""
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}&email={user.email}"
    
    context = {
        'user': user,
        'reset_link': reset_link,
    }
    
    subject = "Réinitialiser votre mot de passe"
    html_message = render_to_string('emails/reset_password.html', context)
    plain_message = f"Cliquez sur ce lien pour réinitialiser votre mot de passe: {reset_link}"
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )
