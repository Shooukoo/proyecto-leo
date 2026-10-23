"""Herramientas del chatbot: cada una consulta al microservicio dueño del dato."""

import re
import time
import uuid

import jwt
import requests
from django.conf import settings


class ServicioError(Exception):
    """Fallo al consultar otro servicio; el mensaje es apto para el LLM/usuario."""


def _token_servicio():
    """Token de vida corta para Tracking, emitido solo tras verificar el pedido del usuario."""
    claims = {
        "user_id": "0",
        "role": "servicio",
        "email": "chatbot@servicio.local",
        "token_type": "access",
        "exp": int(time.time()) + 60,
    }
    return jwt.encode(claims, settings.JWT_SIGNING_KEY, algorithm=settings.JWT_ALGORITHM)


def _get(base, ruta, token, params=None):
    try:
        resp = requests.get(
            f"{base}{ruta}",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=settings.SERVICE_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ServicioError("El servicio no está disponible por ahora.") from exc
    if resp.status_code == 404:
        raise ServicioError("No se encontró información para esa consulta.")
    if resp.status_code in (401, 403):
        raise ServicioError("No tienes permiso para consultar esa información.")
    if not resp.ok:
        raise ServicioError("El servicio respondió con un error.")
    return resp.json()


def _resumen_pedido(p):
    return {
        "id": p["id"],
        "folio": p["folio"],
        "estado": p["estado"],
        "prioridad": p["prioridad"],
        "descripcion": p["descripcion"],
        "es_cod": p["es_cod"],
        "monto_cod": p["monto_cod"],
        "actualizado": p["actualizado"],
    }


def buscar_pedido(token, referencia):
    """Busca por id numérico o por folio (UUID) con el token del propio usuario."""
    ref = str(referencia).strip().lstrip("#")
    if re.fullmatch(r"\d+", ref):
        return _get(settings.PEDIDOS_URL, f"/api/pedidos/{ref}/", token)
    try:
        folio = str(uuid.UUID(ref))
    except ValueError:
        raise ServicioError("El número de pedido o folio no es válido.") from None
    resultados = _get(settings.PEDIDOS_URL, "/api/pedidos/", token, {"folio": folio})["results"]
    if not resultados:
        raise ServicioError("No se encontró información para esa consulta.")
    return resultados[0]


def consultar_pedido(token, pedido):
    return _resumen_pedido(buscar_pedido(token, pedido))


def ubicacion_pedido(token, pedido):
    p = buscar_pedido(token, pedido)  # valida que el pedido es visible para el usuario
    if p["estado"] != "en_ruta":
        return {
            "pedido_id": p["id"],
            "estado": p["estado"],
            "ubicacion": None,
            "nota": "Solo hay ubicación mientras el pedido está en ruta.",
        }
    ubic = _get(
        settings.TRACKING_URL, "/api/ubicaciones/ultima/", _token_servicio(), {"pedido_id": p["id"]}
    )
    return {
        "pedido_id": p["id"],
        "estado": p["estado"],
        "ubicacion": {
            "latitud": ubic["latitud"],
            "longitud": ubic["longitud"],
            "timestamp": ubic["timestamp"],
        },
    }


def listar_mis_pedidos(token, estado=None):
    params = {"estado": estado} if estado else {}
    datos = _get(settings.PEDIDOS_URL, "/api/pedidos/", token, params)
    return {"total": datos["count"], "pedidos": [_resumen_pedido(p) for p in datos["results"][:10]]}


HERRAMIENTAS = {
    "consultar_pedido": consultar_pedido,
    "ubicacion_pedido": ubicacion_pedido,
    "listar_mis_pedidos": listar_mis_pedidos,
}

# Declaraciones neutrales al proveedor (JSON Schema) para function calling.
DECLARACIONES = [
    {
        "name": "consultar_pedido",
        "description": "Consulta el estado de un pedido por su número (id) o folio UUID.",
        "parameters": {
            "type": "object",
            "properties": {
                "pedido": {"type": "string", "description": "Número o folio del pedido"}
            },
            "required": ["pedido"],
        },
    },
    {
        "name": "ubicacion_pedido",
        "description": "Obtiene la última ubicación conocida del repartidor de un pedido en ruta.",
        "parameters": {
            "type": "object",
            "properties": {
                "pedido": {"type": "string", "description": "Número o folio del pedido"}
            },
            "required": ["pedido"],
        },
    },
    {
        "name": "listar_mis_pedidos",
        "description": "Lista los pedidos del usuario, opcionalmente por estado.",
        "parameters": {
            "type": "object",
            "properties": {
                "estado": {
                    "type": "string",
                    "enum": ["creado", "en_ruta", "entregado", "incidencia", "devuelto"],
                }
            },
        },
    },
    {
        "name": "escalar_a_humano",
        "description": "Transfiere la conversación a un agente humano cuando no puedes resolver.",
        "parameters": {
            "type": "object",
            "properties": {"motivo": {"type": "string"}},
            "required": ["motivo"],
        },
    },
]
