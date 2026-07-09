from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ('system', 'Système'),
        ('saved_search', 'Recherche sauvegardée'),
        ('price_drop', 'Baisse de prix'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Module IA #7 : notifications intelligentes
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    bien = models.ForeignKey('biens.Bien', on_delete=models.SET_NULL, related_name='notifications', blank=True, null=True)
    dedup_key = models.CharField(max_length=255, blank=True, db_index=True)

    def __str__(self):
        return f"Notification {self.id} for {self.user.username}"
