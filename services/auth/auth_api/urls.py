from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("users", views.UsuarioViewSet)

urlpatterns = [
    path("auth/register/", views.RegistroView.as_view(), name="registro"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/refresh/", views.RefreshView.as_view(), name="refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/me/", views.PerfilView.as_view(), name="me"),
    path("auth/change-password/", views.CambioPasswordView.as_view(), name="change-password"),
] + router.urls
