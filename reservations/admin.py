from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'bien', 'date', 'status', 'created_at')
    list_filter = ('status', 'date', 'created_at')
    search_fields = ('utilisateur__username', 'bien__titre', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    fieldsets = (
        ('Réservation', {
            'fields': ('utilisateur', 'bien', 'date', 'message')
        }),
        ('Statut', {
            'fields': ('status',)
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('utilisateur', 'bien')

    actions = ['marquer_comme_confirmed', 'marquer_comme_cancelled']

    def marquer_comme_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, f"{queryset.count()} réservation(s) marquée(s) comme confirmée(s).")
    marquer_comme_confirmed.short_description = "Marquer les réservations sélectionnées comme confirmées"

    def marquer_comme_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"{queryset.count()} réservation(s) marquée(s) comme annulée(s).")
    marquer_comme_cancelled.short_description = "Marquer les réservations sélectionnées comme annulées"
