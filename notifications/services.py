from .models import Notification


def notify(user, message):
    """Crée une notification pour un utilisateur. Ne lève jamais d'exception :
    un échec de notification ne doit jamais faire planter l'action métier
    qui l'a déclenchée (message envoyé, réservation confirmée, ...)."""
    if user is None:
        return
    try:
        Notification.objects.create(user=user, message=message)
    except Exception:
        pass
