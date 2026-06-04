from django.contrib import admin
from .models import RecommendationIA


@admin.register(RecommendationIA)
class RecommendationIAAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'ville', 'type_bien', 'budget_min', 'budget_max', 'score', 'created_at')
    list_filter = ('type_bien', 'ville', 'score', 'created_at')
    search_fields = ('user__username', 'ville', 'type_bien')
    readonly_fields = ('created_at', 'updated_at', 'resultats', 'analyse_ia')
    ordering = ('-created_at',)

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Critères de recherche', {
            'fields': ('budget_min', 'budget_max', 'ville', 'type_bien',
                      'nombre_chambres_min', 'localisation')
        }),
        ('Résultats IA', {
            'fields': ('resultats', 'score', 'analyse_ia'),
            'classes': ('collapse',)
        }),
        ('Historique', {
            'fields': ('historique',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
