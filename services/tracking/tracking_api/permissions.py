from rest_framework.permissions import SAFE_METHODS, BasePermission

ROLES_STAFF = {"operador", "gerente", "admin_sistema"}
ROLES_ESCRITURA = ROLES_STAFF | {"repartidor"}


class TrackingPermission(BasePermission):
    """Escribe: repartidor y staff. Lee: staff y repartidor (los clientes solo por pedido)."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return user.role in ROLES_ESCRITURA or getattr(view, "permite_cliente", False)
        return user.role in ROLES_ESCRITURA
