from rest_framework.routers import DefaultRouter

from .views import EventoViewSet, UbicacionViewSet

router = DefaultRouter()
router.register("ubicaciones", UbicacionViewSet, basename="ubicacion")
router.register("eventos", EventoViewSet, basename="evento")

urlpatterns = router.urls
