from django.contrib import admin
from .models import Agence


@admin.register(Agence)
class AgenceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'proprietaire', 'adresse', 'telephone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('nom', 'proprietaire__username', 'adresse')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'proprietaire')
        }),
        ('Contact', {
            'fields': ('adresse', 'telephone')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('proprietaire')
