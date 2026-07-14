from datetime import timedelta

from django.utils import timezone

from .models import Notification

DEDUP_WINDOW_HOURS = 24


def notify(user, message, type='system', bien=None, reservation=None, conversation_id=''):
    """Crée une notification pour un utilisateur. Ne lève jamais d'exception :
    un échec de notification ne doit jamais faire planter l'action métier
    qui l'a déclenchée (message envoyé, réservation confirmée, ...).

    type/bien/reservation/conversation_id permettent au frontend de rediriger
    l'utilisateur vers l'élément concerné au clic, au lieu de se contenter de
    marquer la notification comme lue sans action."""
    if user is None:
        return
    try:
        Notification.objects.create(
            user=user, message=message, type=type, bien=bien,
            reservation=reservation, conversation_id=conversation_id,
        )
    except Exception:
        pass


def notify_once(user, type, dedup_key, message, bien=None):
    """Module 7 : comme `notify`, mais anti-spam — n'envoie pas deux fois la même
    notification (même dedup_key) au même utilisateur dans une fenêtre de 24h."""
    if user is None:
        return None

    fenetre = timezone.now() - timedelta(hours=DEDUP_WINDOW_HOURS)
    deja_envoyee = Notification.objects.filter(
        user=user,
        type=type,
        dedup_key=dedup_key,
        created_at__gte=fenetre,
    ).exists()
    if deja_envoyee:
        return None

    try:
        return Notification.objects.create(
            user=user,
            message=message,
            type=type,
            dedup_key=dedup_key,
            bien=bien,
        )
    except Exception:
        return None
