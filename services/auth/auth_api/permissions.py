from rest_framework.permissions import BasePermission

from .models import Rol


class EsAdminSistema(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.rol == Rol.ADMIN_SISTEMA)
