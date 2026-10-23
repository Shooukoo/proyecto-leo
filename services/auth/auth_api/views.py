from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .permissions import EsAdminSistema
from .serializers import (
    CambioPasswordSerializer,
    LogoutSerializer,
    PerfilSerializer,
    RegistroSerializer,
    TokenConRolSerializer,
    UserSerializer,
    UsuarioAdminSerializer,
)


class Publica:
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_scope = "auth"


class RegistroView(Publica, generics.CreateAPIView):
    serializer_class = RegistroSerializer

    @extend_schema(responses=UserSerializer)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(Publica, TokenObtainPairView):
    serializer_class = TokenConRolSerializer


class RefreshView(Publica, TokenRefreshView):
    pass


class LogoutView(APIView):
    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            return Response({"refresh": "Token inválido."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PerfilView(generics.RetrieveUpdateAPIView):
    serializer_class = PerfilSerializer

    def get_object(self):
        return self.request.user


class CambioPasswordView(APIView):
    @extend_schema(request=CambioPasswordSerializer, responses={204: None})
    def post(self, request):
        serializer = CambioPasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["password_nueva"])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsuarioAdminSerializer
    permission_classes = [EsAdminSistema]
    filterset_fields = ["rol", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["email", "date_joined"]
