from rest_framework.routers import DefaultRouter

from .views import BienViewSet, DocumentViewSet

router = DefaultRouter()
router.register(r'biens', BienViewSet, basename='bien')
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = router.urls
