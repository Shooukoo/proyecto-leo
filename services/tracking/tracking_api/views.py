from datetime import datetime, timezone

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from . import mongo
from .permissions import ROLES_STAFF, TrackingPermission
from .serializers import EventoSerializer, UbicacionSerializer

PAGE_PARAMS = [
    OpenApiParameter("page", int, description="Número de página (1 por defecto)"),
    OpenApiParameter("page_size", int, description="Tamaño de página (máx. 100)"),
    OpenApiParameter("ordering", str, description="Campo; prefijo '-' para descendente"),
]


def _int_param(request, name, default=None, minimo=1, maximo=None):
    raw = request.query_params.get(name)
    if raw in (None, ""):
        return default
    try:
        valor = int(raw)
    except ValueError:
        raise ValidationError({name: "Debe ser un entero."}) from None
    if valor < minimo or (maximo and valor > maximo):
        raise ValidationError({name: "Valor fuera de rango."})
    return valor


def _fecha_param(request, name):
    raw = request.query_params.get(name)
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError({name: "Use formato ISO 8601."}) from None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class MongoViewSet(viewsets.ViewSet):
    """CRUD sobre una colección Mongo con paginación, filtros y orden."""

    repo = None
    serializer_class = None
    filtros_enteros = ()
    campos_orden = ("timestamp",)
    orden_default = "-timestamp"
    requiere_repartidor = True
    permission_classes = [TrackingPermission]

    # --- utilidades ---
    def _filtro(self, request):
        filtro = {}
        for campo in self.filtros_enteros:
            valor = _int_param(request, campo)
            if valor is not None:
                filtro[campo] = valor
        desde, hasta = _fecha_param(request, "desde"), _fecha_param(request, "hasta")
        if desde or hasta:
            filtro["timestamp"] = {
                **({"$gte": desde} if desde else {}),
                **({"$lte": hasta} if hasta else {}),
            }
        return filtro

    def _orden(self, request):
        raw = request.query_params.get("ordering", self.orden_default)
        campo = raw.lstrip("-")
        if campo not in self.campos_orden:
            raise ValidationError({"ordering": f"Campos permitidos: {list(self.campos_orden)}"})
        return campo, raw.startswith("-")

    def _preparar(self, request, data):
        """Un repartidor solo puede escribir con su propio id."""
        if request.user.role == "repartidor":
            data["repartidor_id"] = request.user.id
        elif self.requiere_repartidor and "repartidor_id" not in data:
            raise ValidationError({"repartidor_id": "Este campo es requerido."})
        return data

    def _obtener_o_404(self, pk):
        doc = self.repo.get(pk)
        if doc is None:
            raise NotFound("Documento no encontrado.")
        return doc

    def _verificar_propiedad(self, request, doc):
        if request.user.role == "repartidor" and doc.get("repartidor_id") != request.user.id:
            raise PermissionDenied("Solo puedes modificar tus propios registros.")

    # --- acciones CRUD ---
    @extend_schema(parameters=PAGE_PARAMS)
    def list(self, request):
        page = _int_param(request, "page", 1)
        size = _int_param(request, "page_size", 20, maximo=100)
        total, results = self.repo.list(
            self._filtro(request), self._orden(request), (page - 1) * size, size
        )
        return Response({"count": total, "page": page, "page_size": size, "results": results})

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = self._preparar(request, dict(serializer.validated_data))
        return Response(self.repo.create(data), status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        return Response(self._obtener_o_404(pk))

    def update(self, request, pk=None, partial=False):
        doc = self._obtener_o_404(pk)
        self._verificar_propiedad(request, doc)
        serializer = self.serializer_class(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        if partial:
            nuevo = self.repo.update(pk, data)
        else:
            data = self._preparar(request, data)
            nuevo = self.repo.replace(pk, data)
        return Response(nuevo)

    def partial_update(self, request, pk=None):
        return self.update(request, pk, partial=True)

    def destroy(self, request, pk=None):
        doc = self._obtener_o_404(pk)
        self._verificar_propiedad(request, doc)
        self.repo.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        parameters=PAGE_PARAMS
        + [
            OpenApiParameter("repartidor_id", int),
            OpenApiParameter("pedido_id", int),
            OpenApiParameter("desde", OpenApiTypes.DATETIME),
            OpenApiParameter("hasta", OpenApiTypes.DATETIME),
        ],
        responses=UbicacionSerializer(many=True),
    ),
    create=extend_schema(request=UbicacionSerializer, responses=UbicacionSerializer),
    retrieve=extend_schema(responses=UbicacionSerializer),
    update=extend_schema(request=UbicacionSerializer, responses=UbicacionSerializer),
    partial_update=extend_schema(request=UbicacionSerializer, responses=UbicacionSerializer),
)
class UbicacionViewSet(MongoViewSet):
    repo = mongo.ubicaciones
    serializer_class = UbicacionSerializer
    filtros_enteros = ("repartidor_id", "pedido_id")
    campos_orden = ("timestamp", "repartidor_id", "velocidad_kmh")
    permite_cliente = True  # solo para la acción `ultima` con pedido_id

    def initial(self, request, *args, **kwargs):
        # Los clientes únicamente pueden usar la acción `ultima` filtrando por pedido.
        self.permite_cliente = self.action == "ultima"
        super().initial(request, *args, **kwargs)

    @extend_schema(
        parameters=[OpenApiParameter("repartidor_id", int), OpenApiParameter("pedido_id", int)],
        responses=UbicacionSerializer,
    )
    @action(detail=False, methods=["get"])
    def ultima(self, request):
        """Última ubicación conocida de un repartidor o de un pedido."""
        filtro = self._filtro(request)
        if not ({"repartidor_id", "pedido_id"} & filtro.keys()):
            raise ValidationError("Indica repartidor_id o pedido_id.")
        if request.user.role not in ROLES_STAFF | {"repartidor"} and "pedido_id" not in filtro:
            raise PermissionDenied("Los clientes deben consultar por pedido_id.")
        _, docs = self.repo.list(filtro, ("timestamp", True), 0, 1)
        if not docs:
            raise NotFound("Sin ubicaciones para ese criterio.")
        return Response(docs[0])

    @extend_schema(responses=UbicacionSerializer(many=True))
    @action(detail=False, methods=["get"])
    def ultimas(self, request):
        """Última ubicación de cada repartidor (vista de flota para el operador)."""
        if request.user.role not in ROLES_STAFF:
            raise PermissionDenied("Solo el personal de operación puede ver la flota.")
        pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$group": {"_id": "$repartidor_id", "doc": {"$first": "$$ROOT"}}},
            {"$sort": {"_id": 1}},
        ]
        docs = []
        for fila in self.repo.col.aggregate(pipeline):
            doc = fila["doc"]
            doc["id"] = str(doc.pop("_id"))
            docs.append(doc)
        return Response(docs)


@extend_schema_view(
    list=extend_schema(
        parameters=PAGE_PARAMS
        + [
            OpenApiParameter("pedido_id", int),
            OpenApiParameter("repartidor_id", int),
            OpenApiParameter("tipo", str),
            OpenApiParameter("desde", OpenApiTypes.DATETIME),
            OpenApiParameter("hasta", OpenApiTypes.DATETIME),
        ],
        responses=EventoSerializer(many=True),
    ),
    create=extend_schema(request=EventoSerializer, responses=EventoSerializer),
    retrieve=extend_schema(responses=EventoSerializer),
    update=extend_schema(request=EventoSerializer, responses=EventoSerializer),
    partial_update=extend_schema(request=EventoSerializer, responses=EventoSerializer),
)
class EventoViewSet(MongoViewSet):
    repo = mongo.eventos
    serializer_class = EventoSerializer
    filtros_enteros = ("pedido_id", "repartidor_id")
    campos_orden = ("timestamp", "tipo", "pedido_id")
    requiere_repartidor = False

    def _filtro(self, request):
        filtro = super()._filtro(request)
        if request.query_params.get("tipo"):
            filtro["tipo"] = request.query_params["tipo"]
        return filtro
