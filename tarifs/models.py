from django.conf import settings
from django.db import models


class Tarif(models.Model):
    DUREE_CHOICES = [
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('semestriel', 'Semestriel'),
        ('annuel', 'Annuel'),
    ]
    
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    duree = models.CharField(max_length=20, choices=DUREE_CHOICES, default='mensuel')
    features = models.JSONField(default=list, blank=True)  # Liste des fonctionnalités incluses
    actif = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} - {self.prix} FCFA/{self.duree}"


class Abonnement(models.Model):
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('expire', 'Expiré'),
        ('annule', 'Annulé'),
        ('suspendu', 'Suspendu'),
    ]
    
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='abonnements')
    tarif = models.ForeignKey(Tarif, on_delete=models.CASCADE, related_name='abonnements')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    auto_renew = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('utilisateur', 'statut')  # Un seul abonnement actif par utilisateur

    def __str__(self):
        return f"{self.utilisateur.username} - {self.tarif.nom} ({self.statut})"
