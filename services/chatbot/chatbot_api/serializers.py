from rest_framework import serializers


class ChatEntradaSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(required=False, allow_null=True)
    mensaje = serializers.CharField(max_length=1000, trim_whitespace=True)


class ChatSalidaSerializer(serializers.Serializer):
    conversation_id = serializers.CharField()
    respuesta = serializers.CharField()
    herramientas_usadas = serializers.ListField(child=serializers.CharField())
    escalado = serializers.BooleanField()


class MensajeSerializer(serializers.Serializer):
    rol = serializers.ChoiceField(choices=["usuario", "asistente"])
    texto = serializers.CharField()
    herramientas = serializers.ListField(child=serializers.CharField(), required=False)
    timestamp = serializers.DateTimeField()


class ConversacionSerializer(serializers.Serializer):
    id = serializers.CharField()
    usuario_id = serializers.IntegerField()
    estado = serializers.ChoiceField(choices=["abierta", "escalada"])
    mensajes = MensajeSerializer(many=True)
    creado = serializers.DateTimeField()
    actualizado = serializers.DateTimeField()
