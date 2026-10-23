import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from auth_api.models import Rol, User

PASSWORD = "Contraseña-Segura-42"


@pytest.fixture(autouse=True)
def limpiar_throttle():
    cache.clear()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def usuario(db):
    return User.objects.create_user("ana@example.com", PASSWORD, rol=Rol.OPERADOR)


@pytest.fixture
def admin_sistema(db):
    return User.objects.create_user("root@example.com", PASSWORD, rol=Rol.ADMIN_SISTEMA)


def login(api, email, password=PASSWORD):
    return api.post("/api/auth/login/", {"email": email, "password": password}, format="json")


@pytest.fixture
def api_usuario(api, usuario):
    token = login(api, usuario.email).json()["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api


@pytest.fixture
def api_admin(api, admin_sistema):
    token = login(api, admin_sistema.email).json()["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api
