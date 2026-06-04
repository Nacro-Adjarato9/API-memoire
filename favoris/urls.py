from rest_framework.routers import DefaultRouter

from .views import FavoriViewSet

router = DefaultRouter()
router.register(r'favoris', FavoriViewSet, basename='favori')

urlpatterns = router.urls
