from django.core.management.base import BaseCommand

from ia.services import compute_trends


class Command(BaseCommand):
    help = "Module 6 : calcule les tendances de marché (prix moyen par ville/type) et les met en cache."

    def handle(self, *args, **options):
        index = compute_trends()
        self.stdout.write(self.style.SUCCESS(f"{len(index)} segment(s) ville/type mis à jour dans le cache."))
