from django.conf import settings
from django.db import models

from biens.models import Bien


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name='reservations')
    date = models.DateField()
    message = models.TextField(blank=True)
    # Une demande de visite est auto-confirmée dès sa création (pas de validation
    # manuelle du propriétaire requise) ; celui-ci garde la possibilité d'annuler
    # via l'endpoint de mise à jour de statut si besoin.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reservation {self.id} - {self.bien} - {self.status}"
