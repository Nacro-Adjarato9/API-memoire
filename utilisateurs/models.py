from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('locataire', 'Locataire'),
        ('proprietaire', 'Propriétaire'),
        ('agent', 'Agent Immobilier'),
        ('agence', 'Agence Immobilière'),
        ('admin', 'Administrateur'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='locataire')
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=255, blank=True, null=True)
    verification_token_expires = models.DateTimeField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True)
    date_naissance = models.DateField(blank=True, null=True)
    sexe = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    compte_actif = models.BooleanField(default=True)

    def __str__(self):
        return f"Profile for {self.user.username} - {self.role}"


class ProfilProprietaire(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_proprietaire')
    
    # Infos personnelles
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    TYPE_PROPRIETAIRE_CHOICES = [
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise'),
    ]
    type_proprietaire = models.CharField(max_length=20, choices=TYPE_PROPRIETAIRE_CHOICES, default='particulier')
    date_naissance = models.DateField(blank=True, null=True)
    sexe = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')], blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    
    # Adresse
    pays = models.CharField(max_length=100, default='Côte d\'Ivoire')
    ville = models.CharField(max_length=100)
    commune = models.CharField(max_length=100, blank=True)
    quartier = models.CharField(max_length=100, blank=True)
    adresse_complete = models.TextField(blank=True)
    
    # Vérification identité
    TYPE_PIECE_CHOICES = [
        ('cni', 'Carte Nationale d\'Identité'),
        ('passeport', 'Passeport'),
    ]
    type_piece = models.CharField(max_length=20, choices=TYPE_PIECE_CHOICES, blank=True)
    numero_piece = models.CharField(max_length=50, blank=True)
    photo_piece_recto = models.ImageField(upload_to='documents/', blank=True, null=True)
    photo_piece_verso = models.ImageField(upload_to='documents/', blank=True, null=True)
    selfie_verification = models.ImageField(upload_to='documents/', blank=True, null=True)
    statut_verification = models.CharField(max_length=20, choices=[
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
    ], default='en_attente')
    date_verification = models.DateTimeField(blank=True, null=True)
    
    # Infos immobilières
    nombre_biens = models.PositiveIntegerField(default=0)
    type_biens = models.CharField(max_length=200, blank=True)  # appartement, maison, etc.
    zone_activite = models.CharField(max_length=200, blank=True)
    
    # Statistiques
    nombre_locations = models.PositiveIntegerField(default=0)
    revenu_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Sécurité
    compte_verifie = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Profil Propriétaire: {self.nom} {self.prenom}"


class ProfilAgence(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_agence')
    
    # Infos générales
    nom_agence = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    description = models.TextField(blank=True)
    
    # Contact
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)
    
    # Localisation
    pays = models.CharField(max_length=100, default='Côte d\'Ivoire')
    ville = models.CharField(max_length=100)
    commune = models.CharField(max_length=100, blank=True)
    quartier = models.CharField(max_length=100, blank=True)
    adresse_complete = models.TextField(blank=True)
    
    # Infos légales
    numero_registre_commerce = models.CharField(max_length=100, blank=True)
    numero_contribuable = models.CharField(max_length=100, blank=True)
    document_legal = models.FileField(upload_to='documents/', blank=True, null=True)
    date_creation_agence = models.DateField(blank=True, null=True)
    
    # Vérification
    statut_verification = models.CharField(max_length=20, choices=[
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
    ], default='en_attente')
    date_verification = models.DateTimeField(blank=True, null=True)
    
    # Activité
    nombre_biens = models.PositiveIntegerField(default=0)
    type_biens = models.CharField(max_length=200, blank=True)
    zones_couvertes = models.TextField(blank=True)
    
    # Équipe
    nombre_agents = models.PositiveIntegerField(default=0)
    responsable_agence = models.CharField(max_length=100, blank=True)
    
    # Performance
    nombre_transactions = models.PositiveIntegerField(default=0)
    revenu_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    # Sécurité
    compte_verifie = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Profil Agence: {self.nom_agence}"


class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255, unique=True)
    date_expiration = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        return timezone.now() > self.date_expiration
    
    def __str__(self):
        return f"Password reset for {self.user.username}"


class Profil(models.Model):
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    photo = models.ImageField(upload_to='profils/', blank=True, null=True)
    adresse = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"


class Visite(models.Model):
    STATUT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('effectuee', 'Effectuée'),
        ('annulee', 'Annulée'),
    ]

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visites')
    bien = models.ForeignKey('biens.Bien', on_delete=models.CASCADE, related_name='visites')
    date_visite = models.DateField()
    heure_visite = models.TimeField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='planifiee')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Visite {self.bien} par {self.utilisateur.username} le {self.date_visite}"


class Paiement(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('succes', 'Succès'),
        ('echec', 'Échec'),
    ]
    METHODE_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('carte', 'Carte'),
    ]

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paiements')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    methode = models.CharField(max_length=50, choices=METHODE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    reference_transaction = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, blank=True)
    payment_url = models.URLField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.methode} {self.montant} - {self.statut}"


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('abonnement', 'Abonnement'),
        ('reservation', 'Reservation'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('succes', 'Succès'),
        ('echec', 'Échec'),
    ]

    paiement = models.ForeignKey(Paiement, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.type} - {self.statut}"


class Ville(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    pays = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


class Quartier(models.Model):
    nom = models.CharField(max_length=100)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name='quartiers')

    class Meta:
        unique_together = ('nom', 'ville')

    def __str__(self):
        return f"{self.nom} ({self.ville.nom})"


class Ticket(models.Model):
    STATUT_CHOICES = [
        ('ouvert', 'Ouvert'),
        ('ferme', 'Fermé'),
    ]

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    sujet = models.CharField(max_length=255)
    message = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ouvert')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sujet} - {self.statut}"


class Signalement(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signalements')
    bien = models.ForeignKey('biens.Bien', on_delete=models.CASCADE, related_name='signalements', blank=True, null=True, default=None)
    raison = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now, blank=True, null=True)

    def __str__(self):
        cible_repr = self.bien if self.bien else 'bien inconnu'
        return f"Signalement {self.id} - {cible_repr}"


class HistoriqueRecherche(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historique_recherches')
    critere_recherche = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Historique recherche {self.id} pour {self.utilisateur.username}"


# Signal to create UserProfile when a User is created
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

