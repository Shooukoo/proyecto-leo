import logging
from functools import partial

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import llm, services
from .mongo import ahora, conversaciones
from .serializers import (
    ChatEntradaSerializer,
    ChatSalidaSerializer,
    ConversacionSerializer,
)

logger = logging.getLogger(__name__)

ROLES_STAFF = {"operador", "gerente", "admin_sistema"}
RESPUESTA_ESCALADA = "Tu conversación ya fue transferida a un agente humano; te responderá pronto."


def _cargar(request, conversation_id):
    """Un usuario solo ve sus conversaciones; el staff ve todas."""
    conv = conversaciones.obtener(conversation_id)
    if conv is None or (
        request.user.role not in ROLES_STAFF and conv["usuario_id"] != request.user.id
    ):
        raise NotFound("Conversación no encontrada.")
    return conv


class ChatView(APIView):
    @extend_schema(request=ChatEntradaSerializer, responses=ChatSalidaSerializer)
    def post(self, request):
        entrada = ChatEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        mensaje = entrada.validated_data["mensaje"]
        conv_id = entrada.validated_data.get("conversation_id")
        conv = _cargar(request, conv_id) if conv_id else conversaciones.crear(request.user.id)

        token = request.auth
        mensaje_usuario = {"rol": "usuario", "texto": mensaje, "timestamp": ahora()}

        if conv["estado"] == "escalada":
            conversaciones.agregar_mensajes(
                conv["id"],
                [
                    mensaje_usuario,
                    {
                        "rol": "asistente",
                        "texto": RESPUESTA_ESCALADA,
                        "herramientas": [],
                        "timestamp": ahora(),
                    },
                ],
            )
            return Response(self._salida(conv["id"], RESPUESTA_ESCALADA, [], True))

        funciones = {nombre: partial(fn, token) for nombre, fn in services.HERRAMIENTAS.items()}
        ejecutar = llm.Ejecutor(funciones)
        try:
            texto = llm.get_provider().responder(conv["mensajes"], mensaje, ejecutar)
        except Exception:
            logger.exception("Fallo del proveedor de IA")
            # Fallo del proveedor de IA: se escala en vez de dejar al usuario sin respuesta.
            if "escalar_a_humano" not in ejecutar.usadas:
                ejecutar.usadas.append("escalar_a_humano")
            ejecutar.escalado = True
            texto = "No pude atender tu consulta en este momento; te paso con un agente humano."

        conversaciones.agregar_mensajes(
            conv["id"],
            [
                mensaje_usuario,
                {
                    "rol": "asistente",
                    "texto": texto,
                    "herramientas": ejecutar.usadas,
                    "timestamp": ahora(),
                },
            ],
            estado="escalada" if ejecutar.escalado else None,
        )
        return Response(self._salida(conv["id"], texto, ejecutar.usadas, ejecutar.escalado))

    @staticmethod
    def _salida(conv_id, texto, herramientas, escalado):
        return {
            "conversation_id": conv_id,
            "respuesta": texto,
            "herramientas_usadas": herramientas,
            "escalado": escalado,
        }


class ConversacionListView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter("estado", str, enum=["abierta", "escalada"]),
            OpenApiParameter("page", int),
            OpenApiParameter("page_size", int),
        ],
        responses=ConversacionSerializer(many=True),
    )
    def get(self, request):
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
            size = min(max(int(request.query_params.get("page_size", 20)), 1), 100)
        except ValueError:
            raise ValidationError("page y page_size deben ser enteros.") from None
        filtro = {}
        if request.user.role not in ROLES_STAFF:
            filtro["usuario_id"] = request.user.id
        if request.query_params.get("estado"):
            filtro["estado"] = request.query_params["estado"]
        total, results = conversaciones.listar(filtro, (page - 1) * size, size)
        return Response({"count": total, "page": page, "page_size": size, "results": results})


class ConversacionDetalleView(APIView):
    @extend_schema(
        parameters=[OpenApiParameter("conversation_id", str, OpenApiParameter.PATH)],
        responses=ConversacionSerializer,
    )
    def get(self, request, conversation_id):
        return Response(_cargar(request, conversation_id), status=status.HTTP_200_OK)
