from django.contrib import admin
from .models import Favori


@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'bien', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('utilisateur__username', 'bien__titre')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Favori', {
            'fields': ('utilisateur', 'bien')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('utilisateur', 'bien')
