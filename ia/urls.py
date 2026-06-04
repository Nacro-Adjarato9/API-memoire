from django.urls import path

from .views import (
    IAChatView,
    IAVerifyDocumentView,
    RecommendationAPIView,
    RechercheIAView,
)

urlpatterns = [
    path('ia/recherche/rechercher/', RechercheIAView.as_view({'post': 'rechercher'}), name='ia_recherche'),
    path('ia/chat/', IAChatView.as_view(), name='ia_chat'),
    path('ia/recommendation/', RecommendationAPIView.as_view(), name='ia_recommendation'),
    path('ia/verify-document/', IAVerifyDocumentView.as_view(), name='ia_verify_document'),
    path('ia/verifier-document/verifier/', IAVerifyDocumentView.as_view(), name='ia_verifier_document'),
]
