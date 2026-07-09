from django.contrib import admin
from .models import Bien, Document


@admin.register(Bien)
class BienAdmin(admin.ModelAdmin):
    list_display = ('titre', 'ville', 'type', 'prix', 'statut', 'proprietaire', 'est_suspect', 'score_suspicion', 'created_at')
    list_filter = ('type', 'statut', 'ville', 'est_suspect', 'created_at')
    search_fields = ('titre', 'description', 'ville', 'proprietaire__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'description', 'type', 'statut')
        }),
        ('Prix et localisation', {
            'fields': ('prix', 'ville', 'localisation')
        }),
        ('Caractéristiques', {
            'fields': ('nombre_chambres', 'nombre_salons', 'nombre_cuisines', 'nombre_salles_bain',
                      'superficie', 'etage', 'ascenseur', 'balcon', 'parking')
        }),
        ('Propriétaires', {
            'fields': ('proprietaire', 'agence')
        }),
        ('Détection de fraude (IA)', {
            'fields': ('est_suspect', 'score_suspicion', 'raisons_suspicion')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('proprietaire', 'agence')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_document', 'proprietaire', 'statut_verification', 'created_at')
    list_filter = ('type_document', 'statut_verification', 'created_at')
    search_fields = ('titre', 'proprietaire__username', 'type_document')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Informations document', {
            'fields': ('titre', 'type_document', 'fichier', 'bien')
        }),
        ('Propriétaires', {
            'fields': ('proprietaire', 'agence')
        }),
        ('Vérification', {
            'fields': ('statut_verification', 'commentaires_verification')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )




