from django.contrib import admin
from .models import Avis


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'bien', 'note', 'created_at')
    list_filter = ('note', 'created_at')
    search_fields = ('utilisateur__username', 'bien__titre', 'commentaire')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Avis', {
            'fields': ('utilisateur', 'bien', 'note', 'commentaire')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('utilisateur', 'bien')
