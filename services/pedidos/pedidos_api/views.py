from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import PedidoFilter
from .models import Cliente, Direccion, HistorialEstado, Pedido
from .permissions import LecturaOGestion, PuedeCambiarEstado
from .serializers import (
    CambioEstadoSerializer,
    ClienteSerializer,
    DireccionSerializer,
    HistorialEstadoSerializer,
    PedidoSerializer,
)


class AlcanceClienteMixin:
    """El rol `cliente` solo ve lo que pertenece a su usuario; el resto ve todo."""

    campo_cliente = "usuario_id"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "cliente":
            return qs.filter(**{self.campo_cliente: user.id})
        return qs


class ClienteViewSet(AlcanceClienteMixin, viewsets.ModelViewSet):
    queryset = Cliente.objects.prefetch_related("direcciones")
    serializer_class = ClienteSerializer
    permission_classes = [LecturaOGestion]
    search_fields = ["nombre", "telefono", "email"]
    ordering_fields = ["nombre", "creado"]


class DireccionViewSet(AlcanceClienteMixin, viewsets.ModelViewSet):
    campo_cliente = "cliente__usuario_id"
    queryset = Direccion.objects.select_related("cliente")
    serializer_class = DireccionSerializer
    permission_classes = [LecturaOGestion]
    filterset_fields = ["cliente", "ciudad", "estado", "codigo_postal"]
    search_fields = ["calle", "colonia", "ciudad"]
    ordering_fields = ["ciudad", "colonia"]


class PedidoViewSet(AlcanceClienteMixin, viewsets.ModelViewSet):
    campo_cliente = "cliente__usuario_id"
    queryset = Pedido.objects.select_related("cliente", "direccion_origen", "direccion_destino")
    serializer_class = PedidoSerializer
    permission_classes = [LecturaOGestion]
    filterset_class = PedidoFilter
    search_fields = ["descripcion", "cliente__nombre", "direccion_destino__colonia"]
    ordering_fields = ["creado", "prioridad", "peso_kg", "estado"]

    def get_permissions(self):
        if self.action == "cambiar_estado":
            return [PuedeCambiarEstado()]
        return super().get_permissions()

    @extend_schema(request=CambioEstadoSerializer, responses=PedidoSerializer)
    @action(detail=True, methods=["post"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        pedido = self.get_object()
        entrada = CambioEstadoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        nuevo = entrada.validated_data["estado"]
        if not pedido.puede_pasar_a(nuevo):
            return Response(
                {"estado": f"Transición inválida: {pedido.estado} → {nuevo}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            HistorialEstado.objects.create(
                pedido=pedido,
                estado_anterior=pedido.estado,
                estado_nuevo=nuevo,
                usuario_id=request.user.id,
                comentario=entrada.validated_data.get("comentario", ""),
            )
            pedido.estado = nuevo
            pedido.save(update_fields=["estado", "actualizado"])
        return Response(PedidoSerializer(pedido).data)

    @extend_schema(responses=HistorialEstadoSerializer(many=True))
    @action(detail=True, methods=["get"], pagination_class=None)
    def historial(self, request, pk=None):
        pedido = self.get_object()
        return Response(HistorialEstadoSerializer(pedido.historial.all(), many=True).data)
