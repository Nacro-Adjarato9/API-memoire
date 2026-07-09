from django.core.management.base import BaseCommand

from ia.services import check_new_matches_and_price_drops


class Command(BaseCommand):
    help = "Module 7 : notifie les nouveaux biens correspondant aux recherches sauvegardées et les baisses de prix sur les favoris."

    def handle(self, *args, **options):
        nb_notifs = check_new_matches_and_price_drops()
        self.stdout.write(self.style.SUCCESS(f"{nb_notifs} notification(s) créée(s)."))
