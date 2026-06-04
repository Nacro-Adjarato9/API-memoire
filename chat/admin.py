from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation_id', 'sender', 'receiver', 'texte_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('sender__username', 'receiver__username', 'texte', 'conversation_id')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Informations message', {
            'fields': ('conversation_id', 'sender', 'receiver', 'texte')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def texte_preview(self, obj):
        return obj.texte[:50] + '...' if len(obj.texte) > 50 else obj.texte
    texte_preview.short_description = 'Texte'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender', 'receiver')
