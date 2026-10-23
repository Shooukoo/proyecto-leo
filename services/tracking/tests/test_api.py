from conftest import cliente_con_rol

UBI = "/api/ubicaciones/"
EVT = "/api/eventos/"
PUNTO = {"latitud": 19.7, "longitud": -101.19}


def test_requiere_autenticacion(api):
    assert api.get(UBI).status_code == 401


def test_repartidor_registra_ubicacion_con_su_propio_id(repartidor):
    resp = repartidor.post(
        UBI, {**PUNTO, "repartidor_id": 99, "extra": {"gps": "ok"}}, format="json"
    )
    assert resp.status_code == 201
    assert resp.json()["repartidor_id"] == 7
    assert resp.json()["extra"] == {"gps": "ok"}  # esquema flexible


def test_validaciones_de_coordenadas(repartidor):
    assert repartidor.post(UBI, {"latitud": 120, "longitud": 0}, format="json").status_code == 400
    assert repartidor.post(UBI, {"latitud": 1}, format="json").status_code == 400


def test_operador_debe_indicar_repartidor(operador):
    assert operador.post(UBI, PUNTO, format="json").status_code == 400
    assert operador.post(UBI, {**PUNTO, "repartidor_id": 3}, format="json").status_code == 201


def test_crud_completo(operador):
    pk = operador.post(UBI, {**PUNTO, "repartidor_id": 3}, format="json").json()["id"]
    assert operador.get(f"{UBI}{pk}/").json()["latitud"] == 19.7
    assert (
        operador.patch(f"{UBI}{pk}/", {"velocidad_kmh": 40}, format="json").json()["velocidad_kmh"]
        == 40
    )
    reemplazo = operador.put(
        f"{UBI}{pk}/", {"latitud": 20, "longitud": -100, "repartidor_id": 3}, format="json"
    )
    assert reemplazo.status_code == 200 and reemplazo.json()["latitud"] == 20
    assert operador.delete(f"{UBI}{pk}/").status_code == 204
    assert operador.get(f"{UBI}{pk}/").status_code == 404
    assert operador.get(f"{UBI}no-es-un-id/").status_code == 404


def test_repartidor_no_modifica_registros_ajenos(operador, repartidor):
    pk = operador.post(UBI, {**PUNTO, "repartidor_id": 3}, format="json").json()["id"]
    assert repartidor.delete(f"{UBI}{pk}/").status_code == 403


def test_listado_filtros_orden_y_paginacion(operador):
    for rid, lat in [(1, 10), (1, 11), (2, 12)]:
        operador.post(
            UBI,
            {"latitud": lat, "longitud": 0, "repartidor_id": rid, "velocidad_kmh": lat},
            format="json",
        )
    todo = operador.get(UBI).json()
    assert todo["count"] == 3
    assert operador.get(UBI, {"repartidor_id": 1}).json()["count"] == 2
    pagina = operador.get(UBI, {"page_size": 2, "page": 2}).json()
    assert len(pagina["results"]) == 1 and pagina["count"] == 3
    orden = operador.get(UBI, {"ordering": "-velocidad_kmh"}).json()["results"]
    assert [d["velocidad_kmh"] for d in orden] == [12, 11, 10]
    assert operador.get(UBI, {"ordering": "inventado"}).status_code == 400
    assert operador.get(UBI, {"repartidor_id": "x"}).status_code == 400


def test_ultima_ubicacion_y_flota(operador):
    for rid, lat, ts in [
        (1, 10, "2026-10-01T10:00:00Z"),
        (1, 11, "2026-10-01T11:00:00Z"),
        (2, 12, "2026-10-01T09:00:00Z"),
    ]:
        operador.post(
            UBI,
            {
                "latitud": lat,
                "longitud": 0,
                "repartidor_id": rid,
                "timestamp": ts,
                "pedido_id": rid,
            },
            format="json",
        )
    assert operador.get(UBI + "ultima/", {"repartidor_id": 1}).json()["latitud"] == 11
    assert operador.get(UBI + "ultima/").status_code == 400
    assert operador.get(UBI + "ultima/", {"repartidor_id": 99}).status_code == 404
    flota = operador.get(UBI + "ultimas/").json()
    assert [(d["repartidor_id"], d["latitud"]) for d in flota] == [(1, 11), (2, 12)]


def test_cliente_no_accede_a_tracking_y_servicio_solo_a_ultima(operador):
    operador.post(UBI, {**PUNTO, "repartidor_id": 1, "pedido_id": 5}, format="json")
    cliente = cliente_con_rol("cliente", user_id=50)
    assert cliente.get(UBI + "ultima/", {"pedido_id": 5}).status_code == 403
    servicio = cliente_con_rol("servicio", user_id=0)
    assert servicio.get(UBI + "ultima/", {"pedido_id": 5}).status_code == 200
    assert servicio.get(UBI).status_code == 403
    assert servicio.post(UBI, PUNTO, format="json").status_code == 403


def test_eventos_esquema_flexible_y_validacion(repartidor):
    foto = repartidor.post(
        EVT,
        {"tipo": "foto", "pedido_id": 5, "datos": {"url": "x.jpg", "bytes": 1024}},
        format="json",
    )
    assert foto.status_code == 201 and foto.json()["datos"]["bytes"] == 1024
    assert (
        repartidor.post(EVT, {"tipo": "incidencia", "pedido_id": 5}, format="json").status_code
        == 400
    )
    ok = repartidor.post(
        EVT,
        {"tipo": "incidencia", "pedido_id": 5, "datos": {"motivo": "Nadie en casa"}},
        format="json",
    )
    assert ok.status_code == 201
    assert repartidor.post(EVT, {"tipo": "otro", "pedido_id": 5}, format="json").status_code == 400
    assert repartidor.get(EVT, {"pedido_id": 5, "tipo": "incidencia"}).json()["count"] == 1
