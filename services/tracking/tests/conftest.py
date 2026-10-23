import time

import jwt
import mongomock
import pytest
from django.conf import settings
from rest_framework.test import APIClient

from tracking_api import mongo


def make_token(role="operador", user_id=1, token_type="access"):
    claims = {
        "user_id": str(user_id),
        "email": f"{role}@example.com",
        "role": role,
        "token_type": token_type,
        "exp": int(time.time()) + 300,
    }
    return jwt.encode(claims, settings.JWT_SIGNING_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture(autouse=True)
def mongo_falso(monkeypatch):
    """Reemplaza MongoDB por mongomock: sin servidor, aislado por prueba."""
    cliente = mongomock.MongoClient(tz_aware=True)
    monkeypatch.setattr(mongo, "_client", cliente)
    for repo in (mongo.ubicaciones, mongo.eventos):
        monkeypatch.setattr(repo, "_indexed", False)
    return cliente


@pytest.fixture
def api():
    return APIClient()


def cliente_con_rol(rol, user_id=1):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(rol, user_id)}")
    return c


@pytest.fixture
def operador():
    return cliente_con_rol("operador")


@pytest.fixture
def repartidor():
    return cliente_con_rol("repartidor", user_id=7)
