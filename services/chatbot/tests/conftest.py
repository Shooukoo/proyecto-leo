import time

import jwt
import mongomock
import pytest
from django.conf import settings
from rest_framework.test import APIClient

from chatbot_api import mongo


def make_token(role="cliente", user_id=50):
    claims = {
        "user_id": str(user_id),
        "email": f"{role}@example.com",
        "role": role,
        "token_type": "access",
        "exp": int(time.time()) + 300,
    }
    return jwt.encode(claims, settings.JWT_SIGNING_KEY, algorithm=settings.JWT_ALGORITHM)


def cliente_api(role="cliente", user_id=50):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(role, user_id)}")
    return c


@pytest.fixture(autouse=True)
def mongo_falso(monkeypatch):
    monkeypatch.setattr(mongo, "_client", mongomock.MongoClient(tz_aware=True))


class RespuestaFalsa:
    def __init__(self, data, status_code=200):
        self._data, self.status_code = data, status_code
        self.ok = status_code < 400

    def json(self):
        return self._data


PEDIDO = {
    "id": 5,
    "folio": "3f2b0c1e-7a54-4c1c-9a3d-2f6f5b5a1c11",
    "estado": "en_ruta",
    "prioridad": "alta",
    "descripcion": "Caja",
    "es_cod": False,
    "monto_cod": None,
    "actualizado": "2026-10-01T10:00:00Z",
}
UBICACION = {"latitud": 19.7, "longitud": -101.19, "timestamp": "2026-10-01T10:05:00Z"}


@pytest.fixture
def servicios_falsos(monkeypatch):
    """Simula Pedidos y Tracking; registra las llamadas para verificar tokens y rutas."""
    llamadas = []

    def fake_get(url, params=None, headers=None, timeout=None):
        llamadas.append((url, params, headers["Authorization"]))
        if url.endswith("/api/pedidos/5/"):
            return RespuestaFalsa(PEDIDO)
        if url.endswith("/api/pedidos/"):
            ok = (params or {}).get("folio") == PEDIDO["folio"] or not params
            return RespuestaFalsa({"count": int(ok), "results": [PEDIDO] if ok else []})
        if url.endswith("/api/ubicaciones/ultima/"):
            return RespuestaFalsa(UBICACION)
        return RespuestaFalsa({}, 404)

    monkeypatch.setattr("chatbot_api.services.requests.get", fake_get)
    return llamadas
