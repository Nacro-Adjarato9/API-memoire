from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_verification_email(user, token):
    """Send verification email to user"""
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}&email={user.email}"
    
    context = {
        'user': user,
        'verification_link': verification_link,
        'expiry_hours': 24,
    }
    
    subject = "Vérifiez votre adresse email"
    html_message = render_to_string('emails/verify_email.html', context)
    plain_message = f"Cliquez sur ce lien pour vérifier votre email: {verification_link}"
    
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
