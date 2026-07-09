from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    IAChatView,
    IAVerifyDocumentView,
    RecommendationAPIView,
    RechercheIAView,
    MapLogementsAPIView,
    GeocoderAPIView,
    BudgetAdvisoryView,
    RecommendationIAViewSet,
    ZoneSuggestionsView,
    RecommendationsPersonnaliseesView,
    TrendView,
)

router = DefaultRouter()
router.register(r'recommendations', RecommendationIAViewSet, basename='recommendation-ia')

urlpatterns = [
    path('', include(router.urls)),
    # Recherche intelligente
    path('recherche/rechercher/', RechercheIAView.as_view({'post': 'rechercher'}), name='ia_recherche'),

    # Suggestion de zones voisines (module 5)
    path('suggestions-zone/', ZoneSuggestionsView.as_view(), name='ia_suggestions_zone'),

    # Recommandations personnalisées (module 2)
    path('recommandations-personnalisees/', RecommendationsPersonnaliseesView.as_view(), name='ia_recommandations_personnalisees'),

    # Analyse des tendances (module 6)
    path('tendances/', TrendView.as_view(), name='ia_tendances'),

    # Chat immobilier
    path('chat/', IAChatView.as_view(), name='ia_chat'),

    # Carte OpenStreetMap / Leaflet
    path('map/', MapLogementsAPIView.as_view(), name='ia_map'),
    path('geocoder/', GeocoderAPIView.as_view(), name='ia_geocoder'),

    # Recommandation IA
    path('recommendation/', RecommendationAPIView.as_view(), name='ia_recommendation'),

    # Conseil budgétaire IA
    path('budget-advisory/', BudgetAdvisoryView.as_view(), name='ia_budget_advisory'),

    # Vérification de documents
    path('verify-document/', IAVerifyDocumentView.as_view(), name='ia_verify_document'),
    path('verifier-document/verifier/', IAVerifyDocumentView.as_view(), name='ia_verifier_document'),
]
