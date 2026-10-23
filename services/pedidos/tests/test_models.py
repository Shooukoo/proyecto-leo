import pytest

from pedidos_api.models import Pedido


@pytest.mark.django_db
def test_transiciones_validas(cliente, direcciones):
    origen, destino = direcciones
    pedido = Pedido.objects.create(
        cliente=cliente, direccion_origen=origen, direccion_destino=destino, peso_kg=1
    )
    assert pedido.estado == Pedido.Estado.CREADO
    assert pedido.puede_pasar_a(Pedido.Estado.EN_RUTA)
    assert not pedido.puede_pasar_a(Pedido.Estado.ENTREGADO)


@pytest.mark.django_db
def test_estados_finales_no_tienen_salida(cliente, direcciones):
    origen, destino = direcciones
    pedido = Pedido.objects.create(
        cliente=cliente,
        direccion_origen=origen,
        direccion_destino=destino,
        peso_kg=1,
        estado=Pedido.Estado.ENTREGADO,
    )
    assert not any(pedido.puede_pasar_a(e) for e in Pedido.Estado)
