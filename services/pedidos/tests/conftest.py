import time

import jwt
import pytest
from django.conf import settings
from rest_framework.test import APIClient

from pedidos_api.models import Cliente, Direccion


def make_token(role="operador", user_id=1, token_type="access", exp_in=300):
    claims = {
        "user_id": user_id,
        "email": f"{role}@example.com",
        "role": role,
        "token_type": token_type,
        "exp": int(time.time()) + exp_in,
    }
    return jwt.encode(claims, settings.JWT_SIGNING_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def operador(api):
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token('operador')}")
    return api


@pytest.fixture
def cliente(db):
    return Cliente.objects.create(nombre="Ana López", telefono="4431234567")


@pytest.fixture
def direcciones(cliente):
    kwargs = dict(
        cliente=cliente, numero="10", colonia="Centro", ciudad="Morelia", codigo_postal="58000"
    )
    return (
        Direccion.objects.create(calle="Madero", **kwargs),
        Direccion.objects.create(calle="Allende", **kwargs),
    )


@pytest.fixture
def pedido_payload(cliente, direcciones):
    origen, destino = direcciones
    return {
        "cliente": cliente.pk,
        "direccion_origen": origen.pk,
        "direccion_destino": destino.pk,
        "descripcion": "Caja mediana",
        "peso_kg": "2.50",
        "prioridad": "alta",
    }
