"""Validación local del JWT emitido por el servicio auth (sin llamadas de red)."""

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions


class TokenUser:
    """Usuario ligero construido a partir de los claims del token."""

    is_authenticated = True
    is_anonymous = False

    def __init__(self, claims):
        self.id = int(claims["user_id"]) if "user_id" in claims else None
        self.email = claims.get("email", "")
        self.role = claims.get("role", "")
        self.pk = self.id

    def __str__(self):
        return self.email or str(self.id)


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header or header[0].decode().lower() != self.keyword.lower():
            return None
        if len(header) != 2:
            raise exceptions.AuthenticationFailed("Encabezado Authorization inválido.")
        token = header[1].decode()
        try:
            claims = jwt.decode(
                token, settings.JWT_SIGNING_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.PyJWTError as exc:
            raise exceptions.AuthenticationFailed("Token inválido o expirado.") from exc
        if claims.get("token_type", "access") != "access":
            raise exceptions.AuthenticationFailed("Se requiere un token de acceso.")
        return TokenUser(claims), token

    def authenticate_header(self, request):
        return self.keyword


try:
    from drf_spectacular.extensions import OpenApiAuthenticationExtension

    class JWTScheme(OpenApiAuthenticationExtension):
        """Declara el esquema Bearer en OpenAPI para el botón Authorize de Swagger UI."""

        target_class = "chatbot_api.authentication.JWTAuthentication"
        name = "bearerAuth"

        def get_security_definition(self, auto_schema):
            return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}

except ImportError:  # drf-spectacular es opcional en tiempo de ejecución
    pass
