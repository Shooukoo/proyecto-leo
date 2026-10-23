import django_filters

from .models import Pedido


class PedidoFilter(django_filters.FilterSet):
    creado_desde = django_filters.DateFilter(field_name="creado", lookup_expr="date__gte")
    creado_hasta = django_filters.DateFilter(field_name="creado", lookup_expr="date__lte")
    peso_min = django_filters.NumberFilter(field_name="peso_kg", lookup_expr="gte")
    peso_max = django_filters.NumberFilter(field_name="peso_kg", lookup_expr="lte")

    class Meta:
        model = Pedido
        fields = ["folio", "estado", "prioridad", "cliente", "es_cod", "repartidor_id"]
