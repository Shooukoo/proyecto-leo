import pytest
from conftest import make_token

URL = "/api/pedidos/"


@pytest.mark.django_db
def test_requiere_autenticacion(api):
    assert api.get(URL).status_code == 401


@pytest.mark.django_db
def test_token_invalido_rechazado(api):
    api.credentials(HTTP_AUTHORIZATION="Bearer basura")
    assert api.get(URL).status_code == 401


@pytest.mark.django_db
def test_refresh_token_no_sirve_como_acceso(api):
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(token_type='refresh')}")
    assert api.get(URL).status_code == 401


@pytest.mark.django_db
def test_crud_pedido(operador, pedido_payload):
    creado = operador.post(URL, pedido_payload, format="json")
    assert creado.status_code == 201
    assert creado.json()["estado"] == "creado"
    pk = creado.json()["id"]
    assert operador.get(f"{URL}{pk}/").status_code == 200
    assert operador.patch(f"{URL}{pk}/", {"prioridad": "urgente"}, format="json").status_code == 200
    assert operador.delete(f"{URL}{pk}/").status_code == 204


@pytest.mark.django_db
def test_cliente_no_puede_escribir(api, pedido_payload):
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token('cliente')}")
    assert api.post(URL, pedido_payload, format="json").status_code == 403
    assert api.get(URL).status_code == 200


@pytest.mark.django_db
def test_cod_requiere_monto(operador, pedido_payload):
    resp = operador.post(URL, {**pedido_payload, "es_cod": True}, format="json")
    assert resp.status_code == 400
    assert "monto_cod" in resp.json()


@pytest.mark.django_db
def test_origen_distinto_de_destino(operador, pedido_payload):
    pedido_payload["direccion_destino"] = pedido_payload["direccion_origen"]
    assert operador.post(URL, pedido_payload, format="json").status_code == 400


@pytest.mark.django_db
def test_cambio_de_estado_y_historial(operador, pedido_payload):
    pk = operador.post(URL, pedido_payload, format="json").json()["id"]
    ok = operador.post(f"{URL}{pk}/cambiar-estado/", {"estado": "en_ruta"}, format="json")
    assert ok.status_code == 200 and ok.json()["estado"] == "en_ruta"
    malo = operador.post(f"{URL}{pk}/cambiar-estado/", {"estado": "devuelto"}, format="json")
    assert malo.status_code == 400
    historial = operador.get(f"{URL}{pk}/historial/").json()
    assert [h["estado_nuevo"] for h in historial] == ["en_ruta"]


@pytest.mark.django_db
def test_repartidor_puede_cambiar_estado_pero_no_crear(api, operador, pedido_payload):
    pk = operador.post(URL, pedido_payload, format="json").json()["id"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token('repartidor', user_id=7)}")
    assert api.post(URL, pedido_payload, format="json").status_code == 403
    resp = api.post(f"{URL}{pk}/cambiar-estado/", {"estado": "en_ruta"}, format="json")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_filtros_orden_y_paginacion(operador, pedido_payload):
    for prioridad, peso in [("baja", "1"), ("urgente", "5"), ("alta", "3")]:
        operador.post(
            URL, {**pedido_payload, "prioridad": prioridad, "peso_kg": peso}, format="json"
        )
    assert operador.get(URL, {"prioridad": "urgente"}).json()["count"] == 1
    assert operador.get(URL, {"peso_min": "2"}).json()["count"] == 2
    pesos = [p["peso_kg"] for p in operador.get(URL, {"ordering": "peso_kg"}).json()["results"]]
    assert pesos == ["1.00", "3.00", "5.00"]
    assert len(operador.get(URL, {"page_size": 2}).json()["results"]) == 2
    assert operador.get(URL, {"search": "Caja"}).json()["count"] == 3
