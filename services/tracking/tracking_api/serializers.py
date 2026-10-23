from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

TIPOS_EVENTO = ["inicio_ruta", "parada", "entrega", "incidencia", "foto", "firma", "nota"]


class UbicacionSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    repartidor_id = serializers.IntegerField(min_value=1, required=False)
    pedido_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    latitud = serializers.FloatField(min_value=-90, max_value=90)
    longitud = serializers.FloatField(min_value=-180, max_value=180)
    velocidad_kmh = serializers.FloatField(min_value=0, max_value=300, required=False)
    precision_m = serializers.FloatField(min_value=0, required=False)
    bateria_pct = serializers.IntegerField(min_value=0, max_value=100, required=False)
    timestamp = serializers.DateTimeField(default=timezone.now)
    extra = serializers.DictField(required=False, help_text="Campos libres del dispositivo")

    def validate_timestamp(self, value):
        if value > timezone.now() + timedelta(minutes=5):
            raise serializers.ValidationError("El timestamp no puede estar en el futuro.")
        return value


class EventoSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    tipo = serializers.ChoiceField(choices=TIPOS_EVENTO)
    pedido_id = serializers.IntegerField(min_value=1)
    repartidor_id = serializers.IntegerField(min_value=1, required=False)
    timestamp = serializers.DateTimeField(default=timezone.now)
    datos = serializers.DictField(
        required=False,
        help_text="Esquema flexible según el tipo: URL de foto, firma, motivo de incidencia, etc.",
    )

    def validate(self, attrs):
        datos = attrs.get("datos", {})
        if attrs.get("tipo") == "incidencia" and not datos.get("motivo"):
            raise serializers.ValidationError({"datos": "Las incidencias requieren datos.motivo."})
        return attrs
