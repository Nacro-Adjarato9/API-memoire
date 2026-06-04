from rest_framework.routers import DefaultRouter

from .views import TarifViewSet, AbonnementViewSet

router = DefaultRouter()
router.register(r'tarifs', TarifViewSet, basename='tarif')
router.register(r'abonnements', AbonnementViewSet, basename='abonnement')

urlpatterns = router.urls