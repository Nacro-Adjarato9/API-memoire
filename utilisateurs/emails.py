import requests
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def _send_via_brevo(subject, plain_message, html_message, to_email):
    """Envoie via l'API HTTP de Brevo (port 443, jamais bloque par les
    hebergeurs contrairement au SMTP sortant que beaucoup filtrent)."""
    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": settings.BREVO_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "sender": {"email": settings.DEFAULT_FROM_EMAIL, "name": "LogCiv"},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_message,
            "textContent": plain_message,
        },
        timeout=15,
    )
    response.raise_for_status()


def _send_email(subject, plain_message, html_message, to_email):
    if getattr(settings, "BREVO_API_KEY", ""):
        _send_via_brevo(subject, plain_message, html_message, to_email)
    else:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            html_message=html_message,
            fail_silently=False,
        )


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

    _send_email(subject, plain_message, html_message, user.email)


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

    _send_email(subject, plain_message, html_message, user.email)
