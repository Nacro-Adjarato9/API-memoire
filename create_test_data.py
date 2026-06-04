import os
import django
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from utilisateurs.models import UserProfile, ProfilProprietaire, ProfilAgence
from biens.models import Bien, Document
from reservations.models import Reservation
from avis.models import Avis
from favoris.models import Favori
from tarifs.models import Tarif, Abonnement

User = get_user_model()

def create_test_data():
    print("Création des données de test...")

    # Créer des utilisateurs
    # Propriétaire
    proprietaire_user = User.objects.create_user(
        username='proprietaire1',
        email='proprietaire@test.com',
        password='test123456',
        first_name='Jean',
        last_name='Dupont'
    )
    proprietaire_profile = UserProfile.objects.create(
        user=proprietaire_user,
        role='proprietaire',
        telephone='0102030405',
        is_verified=True
    )
    proprietaire_detail = ProfilProprietaire.objects.create(
        user=proprietaire_user,
        nom='Dupont',
        prenom='Jean',
        ville='Abidjan',
        numero_piece='CI123456789',
        statut_verification='valide'
    )

    # Agence
    agence_user = User.objects.create_user(
        username='agence1',
        email='agence@test.com',
        password='test123456',
        first_name='Marie',
        last_name='Konan'
    )
    agence_profile = UserProfile.objects.create(
        user=agence_user,
        role='agence',
        telephone='0102030406',
        is_verified=True
    )
    agence_detail = ProfilAgence.objects.create(
        user=agence_user,
        nom_agence='Konan Immobilier',
        ville='Abidjan',
        numero_registre_commerce='RC123456',
        statut_verification='valide'
    )

    # Locataire
    locataire_user = User.objects.create_user(
        username='locataire1',
        email='locataire@test.com',
        password='test123456',
        first_name='Pierre',
        last_name='Martin'
    )
    locataire_profile = UserProfile.objects.create(
        user=locataire_user,
        role='locataire',
        telephone='0102030407',
        is_verified=True
    )

    print("Utilisateurs créés")

    # Créer des biens
    bien1 = Bien.objects.create(
        titre='Appartement moderne Cocody',
        description='Magnifique appartement 3 pièces en plein centre de Cocody',
        prix=1500000,
        ville='Abidjan',
        localisation='Cocody, Riviera Palmeraie',
        type='appartement',
        statut='disponible',
        proprietaire=proprietaire_user,
        nombre_chambres=3,
        nombre_salons=1,
        nombre_cuisines=1,
        nombre_salles_bain=2,
        superficie=120,
        etage=2,
        ascenseur=True,
        balcon=True,
        parking=True
    )

    bien2 = Bien.objects.create(
        titre='Villa familiale Bassam',
        description='Belle villa 4 chambres avec jardin à Grand-Bassam',
        prix=2500000,
        ville='Grand-Bassam',
        localisation='Zone résidentielle',
        type='maison',
        statut='disponible',
        proprietaire=proprietaire_user,
        nombre_chambres=4,
        nombre_salons=2,
        nombre_cuisines=1,
        nombre_salles_bain=3,
        superficie=200,
        balcon=False,
        parking=True
    )

    bien3 = Bien.objects.create(
        titre='Bureau Plateau',
        description='Local commercial idéal pour entreprise',
        prix=3000000,
        ville='Abidjan',
        localisation='Plateau, Boulevard Lagunaire',
        type='bureau',
        statut='disponible',
        agence=agence_user,
        nombre_chambres=0,
        nombre_salons=1,
        nombre_cuisines=0,
        nombre_salles_bain=2,
        superficie=150,
        etage=5,
        ascenseur=True,
        parking=True
    )

    print("Biens créés")

    # Créer des images
    Image.objects.create(
        bien=bien1,
        url='https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800'
    )
    Image.objects.create(
        bien=bien1,
        url='https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800'
    )
    Image.objects.create(
        bien=bien2,
        url='https://images.unsplash.com/photo-1449844908441-8829872d2607?w=800'
    )

    print("Images créées")

    # Créer des réservations
    reservation1 = Reservation.objects.create(
        utilisateur=locataire_user,
        bien=bien1,
        date='2026-05-01',
        message='Intéressé par cet appartement',
        status='pending'
    )

    print("Réservations créées")

    # Créer des avis
    avis1 = Avis.objects.create(
        utilisateur=locataire_user,
        bien=bien1,
        note=5,
        commentaire='Très bel appartement, bien situé'
    )

    print("Avis créés")

    # Créer des favoris
    Favori.objects.create(
        utilisateur=locataire_user,
        bien=bien2
    )

    print("Favoris créés")

    # Créer des documents
    Document.objects.create(
        titre='Acte de propriété',
        type_document='acte_propriete',
        fichier='documents/acte_propriete.pdf',
        proprietaire=proprietaire_user,
        bien=bien1,
        statut_verification='valide'
    )

    print("Documents créés")

    # Créer des tarifs
    tarif1 = Tarif.objects.create(
        nom='Plan Essentiel',
        description='Plan de base pour les propriétaires',
        prix=5000,
        duree='mensuel',
        features=['Publication de 5 biens', 'Support email', 'Statistiques basiques']
    )

    tarif2 = Tarif.objects.create(
        nom='Plan Premium',
        description='Plan avancé pour les agences',
        prix=15000,
        duree='mensuel',
        features=['Publication illimitée', 'Support prioritaire', 'Statistiques avancées', 'Gestion locataires']
    )

    tarif3 = Tarif.objects.create(
        nom='Plan Annuel',
        description='Plan annuel avec réduction',
        prix=150000,
        duree='annuel',
        features=['Tous les avantages Premium', 'Réduction 20%', 'Formation incluse']
    )

    print("Tarifs créés")

    # Créer un abonnement
    from datetime import timedelta
    from django.utils import timezone
    date_fin = timezone.now() + timedelta(days=30)
    abonnement1 = Abonnement.objects.create(
        utilisateur=proprietaire_user,
        tarif=tarif1,
        date_fin=date_fin,
        statut='actif'
    )

    print("Abonnements créés")

    print("\n=== DONNÉES DE TEST CRÉÉES ===")
    print("Comptes de test :")
    print("- Propriétaire: proprietaire@test.com / test123456")
    print("- Agence: agence@test.com / test123456")
    print("- Locataire: locataire@test.com / test123456")
    print("\nBiens créés: 3")
    print("Réservations: 1")
    print("Avis: 1")
    print("Favoris: 1")
    print("Images: 3")
    print("Documents: 1")
    print("Tarifs: 3")
    print("Abonnements: 1")

if __name__ == '__main__':
    create_test_data()