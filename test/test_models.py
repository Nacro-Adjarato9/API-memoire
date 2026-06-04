from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from biens.models import Bien, Document
from tarifs.models import Abonnement, Tarif
from utilisateurs.models import (
    HistoriqueRecherche,
    Paiement,
    PasswordReset,
    ProfilAgence,
    ProfilProprietaire,
    Quartier,
    Signalement,
    Ticket,
    Transaction,
    UserProfile,
    Ville,
    Visite,
)


User = get_user_model()


class ModelStringTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="StrongPass123!",
        )
        self.owner_profile, _ = ProfilProprietaire.objects.get_or_create(
            user=self.user,
            defaults={
                "nom": "Ama",
                "prenom": "Kone",
                "ville": "Abidjan",
            },
        )
        self.owner_profile.nom = "Ama"
        self.owner_profile.prenom = "Kone"
        self.owner_profile.ville = "Abidjan"
        self.owner_profile.save()

        self.agency_user = User.objects.create_user(
            username="agency",
            email="agency@example.com",
            password="StrongPass123!",
        )
        self.agency_profile, _ = ProfilAgence.objects.get_or_create(
            user=self.agency_user,
            defaults={
                "nom_agence": "Agence Test",
                "ville": "Abidjan",
            },
        )
        self.agency_profile.nom_agence = "Agence Test"
        self.agency_profile.ville = "Abidjan"
        self.agency_profile.save()

        self.bien = Bien.objects.create(
            titre="Appartement Cocody",
            description="Bien test",
            prix=250000,
            ville="Abidjan",
            localisation="Cocody",
            type="appartement",
            statut="disponible",
            proprietaire=self.user,
        )

    def test_userprofile_str(self):
        self.assertIn("owner", str(self.user.profile))

    def test_profil_proprietaire_str(self):
        self.assertEqual(str(self.owner_profile), "Profil Propriétaire: Ama Kone")

    def test_profil_agence_str(self):
        self.assertEqual(str(self.agency_profile), "Profil Agence: Agence Test")

    def test_bien_str(self):
        self.assertEqual(str(self.bien), "Appartement Cocody - Abidjan")

    def test_document_str(self):
        doc = Document.objects.create(
            titre="CNI",
            type_document="cni",
            fichier=SimpleUploadedFile("cni.pdf", b"dummy"),
            proprietaire=self.user,
        )
        self.assertEqual(str(doc), "cni - CNI")

    def test_tarif_str(self):
        tarif = Tarif.objects.create(
            nom="Premium",
            description="Pack premium",
            prix=10000,
            duree="mensuel",
        )
        self.assertEqual(str(tarif), "Premium - 10000 FCFA/mensuel")

    def test_abonnement_str(self):
        tarif = Tarif.objects.create(
            nom="Standard",
            description="Pack standard",
            prix=5000,
            duree="mensuel",
        )
        abonnement = Abonnement.objects.create(
            utilisateur=self.user,
            tarif=tarif,
            date_fin=timezone.now() + timedelta(days=30),
        )
        self.assertIn("owner - Standard", str(abonnement))

    def test_ville_str(self):
        ville = Ville.objects.create(nom="Abidjan", pays="Cote d'Ivoire")
        self.assertEqual(str(ville), "Abidjan")

    def test_quartier_str(self):
        ville = Ville.objects.create(nom="Abidjan", pays="Cote d'Ivoire")
        quartier = Quartier.objects.create(nom="Cocody", ville=ville)
        self.assertEqual(str(quartier), "Cocody (Abidjan)")

    def test_ticket_str(self):
        ticket = Ticket.objects.create(
            utilisateur=self.user,
            sujet="Probleme",
            message="Aide",
        )
        self.assertIn("Probleme", str(ticket))

    def test_signalement_str(self):
        signalement = Signalement.objects.create(
            utilisateur=self.user,
            raison="Spam",
        )
        self.assertIn("Signalement", str(signalement))

    def test_historique_recherche_str(self):
        hist = HistoriqueRecherche.objects.create(
            utilisateur=self.user,
            critere_recherche="studio abidjan",
        )
        self.assertIn("Historique recherche", str(hist))

    def test_password_reset_is_expired_true(self):
        reset = PasswordReset.objects.create(
            user=self.user,
            token="token",
            date_expiration=timezone.now() - timedelta(hours=1),
        )
        self.assertTrue(reset.is_expired())

    def test_password_reset_is_expired_false(self):
        reset = PasswordReset.objects.create(
            user=self.user,
            token="token2",
            date_expiration=timezone.now() + timedelta(hours=1),
        )
        self.assertFalse(reset.is_expired())

    def test_userprofile_defaults_exist(self):
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.role, "locataire")
        self.assertTrue(profile.compte_actif)

    def test_visite_creation(self):
        visite = Visite.objects.create(
            utilisateur=self.user,
            bien=self.bien,
            date_visite=timezone.now().date(),
            heure_visite=timezone.now().time(),
        )
        self.assertIn("Visite", str(visite))

    def test_paiement_string_contains_method(self):
        paiement = Paiement.objects.create(
            utilisateur=self.user,
            montant=15000,
            methode="mobile_money",
            reference_transaction="REF123",
        )
        self.assertIn("mobile_money", str(paiement))

    def test_transaction_string_contains_status(self):
        paiement = Paiement.objects.create(
            utilisateur=self.user,
            montant=15000,
            methode="mobile_money",
            reference_transaction="REF456",
        )
        transaction = Transaction.objects.create(
            paiement=paiement,
            type="reservation",
            statut="succes",
        )
        self.assertIn("reservation", str(transaction))
