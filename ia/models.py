from django.conf import settings
from django.db import models


class RecommendationIA(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations_ia')
    
    # Critères de recherche
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True)
    type_bien = models.CharField(max_length=50, blank=True)
    nombre_chambres_min = models.PositiveIntegerField(blank=True, null=True)
    localisation = models.TextField(blank=True)
    
    # Résultats
    resultats = models.JSONField(blank=True, null=True)  # Liste des biens recommandés
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Score de pertinence
    analyse_ia = models.TextField(blank=True, null=True)  # Analyse détaillée par Grok AI
    
    # Historique
    historique = models.JSONField(blank=True, null=True)  # Historique des recherches
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Recommandation IA pour {self.user.username} - {self.ville}"
