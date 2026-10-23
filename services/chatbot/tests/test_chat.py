import jwt
from conftest import PEDIDO, cliente_api
from django.conf import settings

CHAT = "/api/chat/"


def test_requiere_autenticacion():
    from rest_framework.test import APIClient

    assert APIClient().post(CHAT, {"mensaje": "hola"}, format="json").status_code == 401


def test_validacion_del_contrato():
    api = cliente_api()
    assert api.post(CHAT, {}, format="json").status_code == 400
    assert api.post(CHAT, {"mensaje": "x" * 1001}, format="json").status_code == 400
    assert (
        api.post(CHAT, {"mensaje": "hola", "conversation_id": "zzz"}, format="json").status_code
        == 404
    )


def test_consulta_de_estado_usa_el_servicio_y_el_token_del_usuario(servicios_falsos):
    api = cliente_api()
    resp = api.post(CHAT, {"mensaje": "¿Cuál es el estado de mi pedido 5?"}, format="json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["herramientas_usadas"] == ["consultar_pedido"]
    assert "en_ruta" in data["respuesta"] and data["escalado"] is False
    url, _, auth = servicios_falsos[0]
    assert url.endswith("/api/pedidos/5/") and auth.startswith("Bearer ")


def test_consulta_por_folio(servicios_falsos):
    resp = cliente_api().post(
        CHAT, {"mensaje": f"estado del folio {PEDIDO['folio']}"}, format="json"
    )
    assert "en_ruta" in resp.json()["respuesta"]
    assert servicios_falsos[0][1] == {"folio": PEDIDO["folio"]}


def test_ubicacion_verifica_pedido_y_usa_token_de_servicio(servicios_falsos):
    resp = cliente_api().post(CHAT, {"mensaje": "¿dónde está mi pedido 5?"}, format="json")
    assert resp.json()["herramientas_usadas"] == ["ubicacion_pedido"]
    assert "19.7" in resp.json()["respuesta"]
    assert servicios_falsos[-1][0].endswith("/api/ubicaciones/ultima/")
    token_tracking = servicios_falsos[-1][2].split()[1]
    claims = jwt.decode(token_tracking, settings.JWT_SIGNING_KEY, algorithms=["HS256"])
    assert claims["role"] == "servicio"


def test_error_de_servicio_no_inventa_datos(monkeypatch):
    import requests

    def caido(*a, **k):
        raise requests.ConnectionError()

    monkeypatch.setattr("chatbot_api.services.requests.get", caido)
    resp = cliente_api().post(CHAT, {"mensaje": "estado de mi pedido 5"}, format="json")
    assert "no está disponible" in resp.json()["respuesta"]


def test_escalamiento_a_humano_y_conversacion_bloqueada():
    api = cliente_api()
    primero = api.post(CHAT, {"mensaje": "quiero hablar con un agente"}, format="json").json()
    assert primero["escalado"] is True and primero["herramientas_usadas"] == ["escalar_a_humano"]
    segundo = api.post(
        CHAT,
        {"mensaje": "¿hay alguien?", "conversation_id": primero["conversation_id"]},
        format="json",
    ).json()
    assert segundo["escalado"] is True and segundo["herramientas_usadas"] == []


def test_historial_y_aislamiento_entre_usuarios(servicios_falsos):
    api = cliente_api(user_id=50)
    conv_id = api.post(CHAT, {"mensaje": "pedido 5"}, format="json").json()["conversation_id"]
    api.post(CHAT, {"mensaje": "gracias", "conversation_id": conv_id}, format="json")
    detalle = api.get(f"/api/conversaciones/{conv_id}/").json()
    assert [m["rol"] for m in detalle["mensajes"]] == ["usuario", "asistente"] * 2
    otro = cliente_api(user_id=51)
    assert otro.get(f"/api/conversaciones/{conv_id}/").status_code == 404
    assert (
        otro.post(CHAT, {"mensaje": "hola", "conversation_id": conv_id}, format="json").status_code
        == 404
    )
    assert otro.get("/api/conversaciones/").json()["count"] == 0
    assert api.get("/api/conversaciones/").json()["count"] == 1


def test_operador_ve_cola_de_escaladas():
    cliente_api(user_id=50).post(CHAT, {"mensaje": "necesito una persona"}, format="json")
    cliente_api(user_id=51).post(CHAT, {"mensaje": "hola"}, format="json")
    operador = cliente_api("operador", user_id=1)
    assert operador.get("/api/conversaciones/").json()["count"] == 2
    assert operador.get("/api/conversaciones/", {"estado": "escalada"}).json()["count"] == 1


def test_fallo_del_proveedor_escala(monkeypatch):
    class Roto:
        def responder(self, *a):
            raise RuntimeError("boom")

    monkeypatch.setattr("chatbot_api.llm.get_provider", lambda: Roto())
    data = cliente_api().post(CHAT, {"mensaje": "hola"}, format="json").json()
    assert data["escalado"] is True
