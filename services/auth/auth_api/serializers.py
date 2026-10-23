from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "telefono", "rol", "is_active"]
        read_only_fields = fields


class RegistroSerializer(serializers.ModelSerializer):
    """Registro público: siempre crea usuarios con rol cliente."""

    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "telefono"]

    def validate(self, attrs):
        validate_password(
            attrs["password"], User(**{k: v for k, v in attrs.items() if k != "password"})
        )
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UsuarioAdminSerializer(RegistroSerializer):
    """Alta/edición por el administrador del sistema (puede fijar rol)."""

    password = serializers.CharField(write_only=True, required=False)

    class Meta(RegistroSerializer.Meta):
        fields = RegistroSerializer.Meta.fields + ["rol", "is_active"]

    def validate(self, attrs):
        if "password" in attrs:
            validate_password(attrs["password"])
        elif not self.instance:
            raise serializers.ValidationError({"password": "Este campo es requerido."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "telefono", "rol"]
        read_only_fields = ["id", "email", "rol"]


class CambioPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    password_nueva = serializers.CharField(write_only=True)

    def validate_password_actual(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Contraseña actual incorrecta.")
        return value

    def validate_password_nueva(self, value):
        validate_password(value, self.context["request"].user)
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class TokenConRolSerializer(TokenObtainPairSerializer):
    """Incluye email y rol en el token para que los demás servicios no consulten a auth."""

    username_field = User.USERNAME_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.rol
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
