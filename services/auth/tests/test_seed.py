import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from auth_api.models import User


@pytest.mark.django_db
def test_seed_demo_crea_un_usuario_por_rol(monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "Demo-Clave-Segura-77")
    call_command("seed_demo")
    call_command("seed_demo")  # idempotente
    assert User.objects.count() == 5
    assert User.objects.get(email="repartidor@paqueteria.test").rol == "repartidor"


@pytest.mark.django_db
def test_seed_demo_exige_password(monkeypatch):
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    with pytest.raises(CommandError):
        call_command("seed_demo")
