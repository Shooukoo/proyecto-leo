from rest_framework import serializers

from .models import Cliente, Direccion, HistorialEstado, Pedido


class DireccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direccion
        fields = "__all__"

    def validate_codigo_postal(self, value):
        if not (value.isdigit() and len(value) == 5):
            raise serializers.ValidationError("El código postal debe tener 5 dígitos.")
        return value

    def validate(self, attrs):
        lat, lng = attrs.get("latitud"), attrs.get("longitud")
        if (lat is None) != (lng is None):
            raise serializers.ValidationError("Latitud y longitud deben enviarse juntas.")
        if lat is not None and not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise serializers.ValidationError("Coordenadas fuera de rango.")
        return attrs


class ClienteSerializer(serializers.ModelSerializer):
    direcciones = DireccionSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = ["id", "nombre", "telefono", "email", "creado", "direcciones"]
        read_only_fields = ["creado"]


class HistorialEstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialEstado
        fields = "__all__"


class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = "__all__"
        read_only_fields = ["folio", "estado", "creado", "actualizado"]

    def validate(self, attrs):
        inst = self.instance
        es_cod = attrs.get("es_cod", inst.es_cod if inst else False)
        monto = attrs.get("monto_cod", inst.monto_cod if inst else None)
        if es_cod and (monto is None or monto <= 0):
            raise serializers.ValidationError(
                {"monto_cod": "Un pedido contra entrega requiere un monto mayor a 0."}
            )
        if not es_cod and monto is not None:
            raise serializers.ValidationError(
                {"monto_cod": "Solo los pedidos contra entrega llevan monto."}
            )
        cliente = attrs.get("cliente", inst.cliente if inst else None)
        destino = attrs.get("direccion_destino", inst.direccion_destino if inst else None)
        origen = attrs.get("direccion_origen", inst.direccion_origen if inst else None)
        if origen and destino and origen.pk == destino.pk:
            raise serializers.ValidationError("Origen y destino no pueden ser la misma dirección.")
        if cliente and origen and origen.cliente_id != cliente.pk:
            raise serializers.ValidationError(
                {"direccion_origen": "La dirección de origen debe pertenecer al cliente."}
            )
        return attrs


class CambioEstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=Pedido.Estado.choices)
    comentario = serializers.CharField(max_length=255, required=False, allow_blank=True)
