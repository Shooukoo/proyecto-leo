from rest_framework.routers import DefaultRouter

from .views import ClienteViewSet, DireccionViewSet, PedidoViewSet

router = DefaultRouter()
router.register("clientes", ClienteViewSet)
router.register("direcciones", DireccionViewSet)
router.register("pedidos", PedidoViewSet)

urlpatterns = router.urls
