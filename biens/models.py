from django.conf import settings
from django.db import models


class Bien(models.Model):
    TYPE_CHOICES = [
        ('appartement', 'Appartement'),
        ('maison', 'Maison'),
        ('terrain', 'Terrain'),
        ('bureau', 'Bureau'),
        ('commerce', 'Commerce'),
    ]
    
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('loue', 'Loué'),
        ('vendu', 'Vendu'),
        ('reserve', 'Réservé'),
    ]
    
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=12, decimal_places=2)
    ville = models.CharField(max_length=100)
    localisation = models.TextField(blank=True)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='appartement')
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('location', 'Location'),
            ('vente', 'Vente'),
            ('location_vente', 'Location / Vente'),
        ],
        default='location',
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='disponible')
    meuble = models.BooleanField(default=False)
    piscine = models.BooleanField(default=False)
    securite = models.BooleanField(default=False)
    proximite = models.CharField(max_length=255, blank=True)
    
    # Caractéristiques
    nombre_chambres = models.PositiveIntegerField(default=0)
    nombre_salons = models.PositiveIntegerField(default=0)
    nombre_cuisines = models.PositiveIntegerField(default=0)
    nombre_salles_bain = models.PositiveIntegerField(default=0)
    superficie = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)  # en m²
    etage = models.PositiveIntegerField(blank=True, null=True)
    ascenseur = models.BooleanField(default=False)
    balcon = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    
    # Relations
    proprietaire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='biens', blank=True, null=True)
    agence = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='biens_agence', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.titre} - {self.ville}"


class Document(models.Model):
    TYPE_CHOICES = [
        ('cni', 'Carte Nationale d\'Identité'),
        ('passeport', 'Passeport'),
        ('registre_commerce', 'Registre de Commerce'),
        ('acte_propriete', 'Acte de Propriété'),
        ('contrat_location', 'Contrat de Location'),
        ('cni_recto', 'CNI / Passeport Recto'),
        ('cni_verso', 'CNI / Passeport Verso'),
        ('justif_propriete', 'Justificatif de Propriété'),
        ('selfie_cni', 'Selfie avec pièce d\'identité'),
        ('facture_cie', 'Facture CIE / SODECI'),
        ('rccm_doc', 'Registre de commerce (RCCM)'),
        ('ncc_doc', 'Numéro Contribuable (NCC)'),
        ('cni_responsable', 'Pièce du responsable'),
        ('autorisation', 'Autorisation d\'exercer'),
        ('logo_agence', 'Logo de l\'agence'),
        ('autre', 'Autre'),
    ]
    
    titre = models.CharField(max_length=255)
    type_document = models.CharField(max_length=50, choices=TYPE_CHOICES)
    fichier = models.FileField(upload_to='documents/')
    proprietaire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents', blank=True, null=True)
    agence = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='documents_agence', blank=True, null=True)
    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name='documents', blank=True, null=True)
    statut_verification = models.CharField(max_length=20, choices=[
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('refuse', 'Refusé'),
    ], default='en_attente')
    commentaires_verification = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.type_document} - {self.titre}"

