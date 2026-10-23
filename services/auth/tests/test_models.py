import pytest

from auth_api.models import Rol, User


@pytest.mark.django_db
def test_usuario_usa_correo_y_rol_cliente_por_defecto():
    user = User.objects.create_user("Nuevo@Example.com", "x")
    assert user.email == "Nuevo@example.com"
    assert user.rol == Rol.CLIENTE
    assert user.check_password("x")


@pytest.mark.django_db
def test_superusuario_es_admin_sistema():
    user = User.objects.create_superuser("root@example.com", "x")
    assert user.rol == Rol.ADMIN_SISTEMA and user.is_staff


@pytest.mark.django_db
def test_correo_obligatorio():
    with pytest.raises(ValueError):
        User.objects.create_user("", "x")
