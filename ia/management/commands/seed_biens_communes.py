from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from biens.models import Bien

User = get_user_model()

# Une commune -> quelques biens variés (prix/type) pour que les modules IA
# (recherche fallback, suggestions de zones, recommandations) aient assez de
# données de test sur toutes les zones, pas seulement Cocody/Bingerville.
COMMUNES_DATA = [
    ("Cocody", "appartement", 350000),
    ("Cocody", "studio", 90000),
    ("Yopougon", "studio", 45000),
    ("Yopougon", "appartement", 120000),
    ("Marcory", "appartement", 180000),
    ("Marcory", "villa", 400000),
    ("Bingerville", "maison", 150000),
    ("Bingerville", "studio", 60000),
    ("Plateau", "bureau", 500000),
    ("Plateau", "appartement", 300000),
    ("Adjame", "studio", 40000),
    ("Adjame", "appartement", 100000),
    ("Treichville", "appartement", 130000),
    ("Treichville", "studio", 55000),
    ("Koumassi", "maison", 110000),
    ("Koumassi", "studio", 50000),
    ("Angre", "villa", 450000),
    ("Angre", "appartement", 220000),
    ("Riviera", "appartement", 280000),
    ("Riviera", "studio", 95000),
]


class Command(BaseCommand):
    help = "Ajoute des biens de test dans chaque commune (pour tester recherche/fallback/suggestions IA)."

    def handle(self, *args, **options):
        proprietaire, _ = User.objects.get_or_create(
            username="seed_proprietaire_ia",
            defaults={"email": "seed-ia@logeciv.test"},
        )

        crees = 0
        for ville, type_bien, prix in COMMUNES_DATA:
            titre = f"{type_bien.title()} test IA - {ville}"
            if Bien.objects.filter(titre=titre, ville=ville).exists():
                continue

            Bien.objects.create(
                titre=titre,
                description=f"Bien de test genere pour la commune de {ville}.",
                prix=prix,
                ville=ville,
                commune=ville.lower().replace("é", "e"),
                quartier=ville,
                localisation=ville,
                type=type_bien,
                transaction_type="location",
                statut="disponible",
                nombre_chambres=2 if type_bien != "studio" else 1,
                nombre_salons=1,
                nombre_salles_bain=1,
                superficie=45 if type_bien == "studio" else 90,
                parking=True,
                proprietaire=proprietaire,
            )
            crees += 1

        self.stdout.write(self.style.SUCCESS(f"{crees} bien(s) de test cree(s) (deja presents ignores)."))
