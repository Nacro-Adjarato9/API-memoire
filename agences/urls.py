from rest_framework.routers import DefaultRouter

from .views import AgenceViewSet

router = DefaultRouter()
router.register(r'agences', AgenceViewSet, basename='agence')

urlpatterns = router.urls
