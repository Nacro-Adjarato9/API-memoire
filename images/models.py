from django.db import models

from biens.models import Bien


class Image(models.Model):
    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name='images')
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} for Bien {self.bien_id}"
