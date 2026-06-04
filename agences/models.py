from django.conf import settings
from django.db import models


class Agence(models.Model):
    nom = models.CharField(max_length=255)
    adresse = models.CharField(max_length=255)
    proprietaire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom
