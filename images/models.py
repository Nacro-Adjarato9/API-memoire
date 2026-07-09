from django.db import models

from biens.models import Bien


class Image(models.Model):
    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name='images')
    # 'url' reste utilisable pour référencer une image externe, mais la plupart des
    # images viennent maintenant d'un vrai upload (fichier stocké sur le serveur).
    url = models.URLField(blank=True)
    fichier = models.ImageField(upload_to='biens_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image {self.id} for Bien {self.bien_id}"
