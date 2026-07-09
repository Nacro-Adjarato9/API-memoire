from django.core.management.base import BaseCommand

from biens.models import Bien
from ia.services import evaluate_bien_fraud


class Command(BaseCommand):
    help = "Module 4 : évalue chaque bien disponible avec les règles de détection de fraude et met à jour score_suspicion/est_suspect."

    def handle(self, *args, **options):
        biens = Bien.objects.filter(statut="disponible")
        nb_suspects = 0

        for bien in biens:
            resultat = evaluate_bien_fraud(bien)
            bien.score_suspicion = resultat["score_suspicion"]
            bien.est_suspect = resultat["est_suspect"]
            bien.raisons_suspicion = resultat["raisons"]
            bien.save(update_fields=["score_suspicion", "est_suspect", "raisons_suspicion"])
            if resultat["est_suspect"]:
                nb_suspects += 1

        self.stdout.write(
            self.style.SUCCESS(f"{biens.count()} bien(s) analysé(s), {nb_suspects} marqué(s) suspect(s).")
        )
