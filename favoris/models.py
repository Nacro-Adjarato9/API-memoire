from django.conf import settings
from django.db import models

from biens.models import Bien


class Favori(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoris')
    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name='favoris')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('utilisateur', 'bien')

    def __str__(self):
        return f"Favori {self.id} - {self.bien}"
