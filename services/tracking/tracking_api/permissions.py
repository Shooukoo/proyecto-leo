from rest_framework.permissions import SAFE_METHODS, BasePermission

ROLES_STAFF = {"operador", "gerente", "admin_sistema"}
ROLES_ESCRITURA = ROLES_STAFF | {"repartidor"}
# Token de servicio que emite el chatbot tras verificar que el pedido es del cliente.
ROL_SERVICIO = "servicio"


class TrackingPermission(BasePermission):
    """Escribe: repartidor y staff. Lee: staff y repartidor; `servicio` solo `ultima`."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.role == ROL_SERVICIO:
            return request.method in SAFE_METHODS and getattr(view, "action", None) == "ultima"
        return user.role in ROLES_ESCRITURA
