from rest_framework.permissions import SAFE_METHODS, BasePermission

ROLES_GESTION = {"operador", "gerente", "admin_sistema"}


class LecturaOGestion(BasePermission):
    """Cualquier usuario autenticado lee; solo roles de gestión escriben."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.method in SAFE_METHODS or request.user.role in ROLES_GESTION


class PuedeCambiarEstado(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in ROLES_GESTION | {"repartidor"})
