import jwt
import pytest
from conftest import PASSWORD, login
from django.conf import settings


@pytest.mark.django_db
def test_registro_publico_siempre_crea_cliente(api):
    resp = api.post(
        "/api/auth/register/",
        {"email": "c@example.com", "password": PASSWORD, "rol": "admin_sistema"},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["rol"] == "cliente"
    assert "password" not in resp.json()


@pytest.mark.django_db
def test_registro_rechaza_password_debil_y_correo_duplicado(api, usuario):
    debil = api.post(
        "/api/auth/register/", {"email": "d@example.com", "password": "123"}, format="json"
    )
    assert debil.status_code == 400
    dup = api.post(
        "/api/auth/register/", {"email": usuario.email, "password": PASSWORD}, format="json"
    )
    assert dup.status_code == 400


@pytest.mark.django_db
def test_login_emite_jwt_con_rol_validable_por_otros_servicios(api, usuario):
    data = login(api, usuario.email).json()
    claims = jwt.decode(data["access"], settings.JWT_SIGNING_KEY, algorithms=["HS256"])
    assert claims["role"] == "operador"
    assert int(claims["user_id"]) == usuario.id
    assert claims["token_type"] == "access"
    assert data["user"]["email"] == usuario.email


@pytest.mark.django_db
def test_login_con_credenciales_incorrectas(api, usuario):
    assert login(api, usuario.email, "otra").status_code == 401


@pytest.mark.django_db
def test_me_requiere_token_y_devuelve_perfil(api, api_usuario):
    assert api_usuario.get("/api/auth/me/").json()["rol"] == "operador"
    api_usuario.credentials()
    assert api_usuario.get("/api/auth/me/").status_code == 401


@pytest.mark.django_db
def test_me_no_permite_escalar_rol(api_usuario):
    resp = api_usuario.patch(
        "/api/auth/me/", {"rol": "admin_sistema", "first_name": "Ana"}, format="json"
    )
    assert resp.status_code == 200
    assert resp.json()["rol"] == "operador" and resp.json()["first_name"] == "Ana"


@pytest.mark.django_db
def test_refresh_y_logout_invalidan_el_refresh(api, usuario):
    refresh = login(api, usuario.email).json()["refresh"]
    nuevo = api.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
    assert nuevo.status_code == 200
    # rotación: el refresh anterior queda en lista negra
    assert api.post("/api/auth/refresh/", {"refresh": refresh}, format="json").status_code == 401
    token = login(api, usuario.email).json()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token['access']}")
    assert (
        api.post("/api/auth/logout/", {"refresh": token["refresh"]}, format="json").status_code
        == 204
    )
    api.credentials()
    assert (
        api.post("/api/auth/refresh/", {"refresh": token["refresh"]}, format="json").status_code
        == 401
    )


@pytest.mark.django_db
def test_cambio_de_password(api, api_usuario, usuario):
    mal = api_usuario.post(
        "/api/auth/change-password/",
        {"password_actual": "no", "password_nueva": "Otra-Clave-Segura-9"},
        format="json",
    )
    assert mal.status_code == 400
    ok = api_usuario.post(
        "/api/auth/change-password/",
        {"password_actual": PASSWORD, "password_nueva": "Otra-Clave-Segura-9"},
        format="json",
    )
    assert ok.status_code == 204
    assert login(api, usuario.email, "Otra-Clave-Segura-9").status_code == 200


@pytest.mark.django_db
def test_gestion_de_usuarios_solo_admin_sistema(api_usuario):
    assert api_usuario.get("/api/users/").status_code == 403


@pytest.mark.django_db
def test_admin_crea_repartidor_filtra_y_desactiva(api_admin):
    creado = api_admin.post(
        "/api/users/",
        {"email": "rep@example.com", "password": PASSWORD, "rol": "repartidor"},
        format="json",
    )
    assert creado.status_code == 201 and creado.json()["rol"] == "repartidor"
    lista = api_admin.get("/api/users/", {"rol": "repartidor"}).json()
    assert lista["count"] == 1
    pk = creado.json()["id"]
    assert (
        api_admin.patch(f"/api/users/{pk}/", {"is_active": False}, format="json").status_code == 200
    )
    api_admin.credentials()
    inactivo = api_admin.post(
        "/api/auth/login/", {"email": "rep@example.com", "password": PASSWORD}, format="json"
    )
    assert inactivo.status_code == 401
