from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    UserProfile,
    ProfilProprietaire,
    ProfilAgence,
    Profil,
    Visite,
    Paiement,
    Transaction,
    Ville,
    Quartier,
    Ticket,
    Signalement,
    HistoriqueRecherche,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_verified', 'created_at')
    list_filter = ('role', 'is_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'role')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'role', 'is_verified')
        }),
        ('Informations personnelles', {
            'fields': ('telephone', 'date_naissance', 'sexe')
        }),
        ('Vérification', {
            'fields': ('verification_token', 'verification_token_expires')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'compte_actif'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProfilProprietaire)
class ProfilProprietaireAdmin(admin.ModelAdmin):
    list_display = ('user', 'nom', 'prenom', 'ville', 'created_at')
    list_filter = ('ville', 'created_at')
    search_fields = ('user__username', 'nom', 'prenom', 'ville')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'date_naissance', 'sexe', 'telephone')
        }),
        ('Adresse', {
            'fields': ('pays', 'ville', 'commune', 'quartier', 'adresse_complete')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProfilAgence)
class ProfilAgenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'nom_agence', 'ville', 'created_at')
    list_filter = ('ville', 'created_at')
    search_fields = ('user__username', 'nom_agence', 'ville')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations agence', {
            'fields': ('nom_agence', 'description', 'ville', 'commune', 'quartier', 'adresse_complete')
        }),
        ('Contact', {
            'fields': ('telephone', 'email', 'site_web')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'nom', 'prenom', 'ville', 'telephone', 'created_at')
    list_filter = ('ville', 'created_at')
    search_fields = ('utilisateur__username', 'nom', 'prenom', 'telephone')
    readonly_fields = ('created_at',)


@admin.register(Visite)
class VisiteAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'bien', 'date_visite', 'heure_visite', 'statut')
    list_filter = ('statut', 'date_visite')
    search_fields = ('utilisateur__username', 'bien__titre')


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'montant', 'methode', 'statut', 'date')
    list_filter = ('methode', 'statut', 'date')
    search_fields = ('utilisateur__username', 'reference_transaction')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('paiement', 'type', 'statut', 'date')
    list_filter = ('type', 'statut', 'date')
    search_fields = ('paiement__reference_transaction',)


@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pays')
    search_fields = ('nom', 'pays')


@admin.register(Quartier)
class QuartierAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville')
    search_fields = ('nom', 'ville__nom')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'sujet', 'statut', 'date')
    list_filter = ('statut', 'date')
    search_fields = ('utilisateur__username', 'sujet')


@admin.register(HistoriqueRecherche)
class HistoriqueRechercheAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'critere_recherche', 'date')
    list_filter = ('date',)
    search_fields = ('utilisateur__username', 'critere_recherche')


@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'bien', 'raison', 'date')
    list_filter = ('date',)
    search_fields = ('utilisateur__username', 'bien__titre', 'raison')
    readonly_fields = ('date',)

    fieldsets = (
        ('Signalement', {
            'fields': ('utilisateur', 'bien', 'raison')
        }),
        ('Métadonnées', {
            'fields': ('date',),
            'classes': ('collapse',)
        }),
    )
