"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import SearchView, StatsView, DashboardView, TypesBienView, LocatairesView, ActeursView

# ViewSets for global API root
from biens.views import BienViewSet, DocumentViewSet
from reservations.views import ReservationViewSet
from chat.views import MessageViewSet
from avis.views import AvisViewSet
from favoris.views import FavoriViewSet
from images.views import ImageViewSet
from notifications.views import NotificationViewSet
from agences.views import AgenceViewSet
from tarifs.views import TarifViewSet, AbonnementViewSet
from ia.views import RecommendationIAViewSet, RechercheIAView
from utilisateurs.views import (
    UtilisateurViewSet,
    ProfilViewSet,
    VisiteViewSet,
    PaiementViewSet,
    TransactionViewSet,
    VilleViewSet,
    QuartierViewSet,
    TicketViewSet,
    SignalementViewSet,
    HistoriqueRechercheViewSet,
)

router = DefaultRouter()
router.register(r'biens', BienViewSet, basename='bien')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'avis', AvisViewSet, basename='avis')
router.register(r'favoris', FavoriViewSet, basename='favori')
router.register(r'images', ImageViewSet, basename='image')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'agences', AgenceViewSet, basename='agence')
router.register(r'tarifs', TarifViewSet, basename='tarif')
router.register(r'abonnements', AbonnementViewSet, basename='abonnement')
router.register(r'ia/recommendations', RecommendationIAViewSet, basename='recommendation_ia')
router.register(r'utilisateurs', UtilisateurViewSet, basename='utilisateur')
router.register(r'profils', ProfilViewSet, basename='profil')
router.register(r'visites', VisiteViewSet, basename='visite')
router.register(r'paiements', PaiementViewSet, basename='paiement')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'villes', VilleViewSet, basename='ville')
router.register(r'quartiers', QuartierViewSet, basename='quartier')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'signalements', SignalementViewSet, basename='signalement')
router.register(r'historique-recherches', HistoriqueRechercheViewSet, basename='historique-recherche')

schema_view = get_schema_view(
   openapi.Info(
      title="LogCiv API",
      default_version='v1',
      description="API REST complète pour la plateforme immobilière LogCiv",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@logciv.ci"),
      license=openapi.License(name="MIT License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', RedirectView.as_view(url='/api/', permanent=False)),
    # path('api-auth/', include('rest_framework.urls')),  # Enlévé - API publique
    path('admin/', admin.site.urls),

    # Documentation Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # APIs (non-ViewSet / extra routes) — doivent être incluses AVANT router.urls, sinon
    # UtilisateurViewSet (utilisateurs/<pk>/) intercepte des routes comme utilisateurs/me/
    # avant qu'elles n'atteignent leur vraie vue (ex: pk="me" → 404 générique).
    path('api/', include('utilisateurs.urls')),
    path('ia/', include('ia.urls')),
    path('api/ia/', include('ia.urls')),
    path('api/', include('notifications.urls')),
    path('api/', include('reservations.urls')),
    path('api/', include('chat.urls')),
    path('api/', include(router.urls)),

    # Utility endpoints
    path('api/search/', SearchView.as_view(), name='search'),
    path('api/recherche/', SearchView.as_view(), name='recherche'),
    path('api/stats/', StatsView.as_view(), name='stats'),
    path('api/dashboard/<str:scope>/', DashboardView.as_view(), name='dashboard'),
    path('api/types-bien/', TypesBienView.as_view(), name='types-bien'),
    path('api/locataires/', LocatairesView.as_view(), name='locataires'),
    path('api/acteurs/', ActeursView.as_view(), name='acteurs'),

    # Démo carte Google Maps (propriétaire place son bien / locataire consulte)
    path(
        'biens/ajouter/',
        TemplateView.as_view(
            template_name='biens/ajouter_bien.html',
            extra_context={'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY},
        ),
        name='biens-ajouter',
    ),
    path(
        'biens/carte/',
        TemplateView.as_view(
            template_name='biens/carte_biens.html',
            extra_context={'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY},
        ),
        name='biens-carte',
    ),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
