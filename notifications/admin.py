from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Notification', {
            'fields': ('user', 'message', 'is_read')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    actions = ['marquer_comme_lu', 'marquer_comme_non_lu']

    def marquer_comme_lu(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} notification(s) marquée(s) comme lue(s).")
    marquer_comme_lu.short_description = "Marquer les notifications sélectionnées comme lues"

    def marquer_comme_non_lu(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} notification(s) marquée(s) comme non lue(s).")
    marquer_comme_non_lu.short_description = "Marquer les notifications sélectionnées comme non lues"