import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Cliente(models.Model):
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Direccion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="direcciones")
    calle = models.CharField(max_length=150)
    numero = models.CharField(max_length=20)
    colonia = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    estado = models.CharField(max_length=100, default="Michoacán")
    codigo_postal = models.CharField(max_length=5)
    referencias = models.TextField(blank=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "direcciones"

    def __str__(self):
        return f"{self.calle} {self.numero}, {self.colonia}, {self.ciudad}"


class Pedido(models.Model):
    class Estado(models.TextChoices):
        CREADO = "creado", "Creado"
        EN_RUTA = "en_ruta", "En ruta"
        ENTREGADO = "entregado", "Entregado"
        INCIDENCIA = "incidencia", "Incidencia"
        DEVUELTO = "devuelto", "Devuelto"

    class Prioridad(models.TextChoices):
        BAJA = "baja", "Baja"
        NORMAL = "normal", "Normal"
        ALTA = "alta", "Alta"
        URGENTE = "urgente", "Urgente"

    # Ciclo de vida del README: creado → en_ruta → entregado / incidencia / devuelto
    TRANSICIONES = {
        Estado.CREADO: {Estado.EN_RUTA},
        Estado.EN_RUTA: {Estado.ENTREGADO, Estado.INCIDENCIA},
        Estado.INCIDENCIA: {Estado.EN_RUTA, Estado.DEVUELTO},
        Estado.ENTREGADO: set(),
        Estado.DEVUELTO: set(),
    }

    folio = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="pedidos")
    direccion_origen = models.ForeignKey(
        Direccion, on_delete=models.PROTECT, related_name="pedidos_origen"
    )
    direccion_destino = models.ForeignKey(
        Direccion, on_delete=models.PROTECT, related_name="pedidos_destino"
    )
    descripcion = models.CharField(max_length=255, blank=True)
    peso_kg = models.DecimalField(
        max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    prioridad = models.CharField(max_length=10, choices=Prioridad, default=Prioridad.NORMAL)
    estado = models.CharField(max_length=12, choices=Estado, default=Estado.CREADO)
    es_cod = models.BooleanField(default=False, help_text="Pago contra entrega")
    monto_cod = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    repartidor_id = models.PositiveIntegerField(
        null=True, blank=True, help_text="ID de usuario (servicio auth) con rol repartidor"
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado"]

    def __str__(self):
        return f"Pedido {self.folio} ({self.estado})"

    def puede_pasar_a(self, nuevo_estado):
        return nuevo_estado in self.TRANSICIONES[self.estado]


class HistorialEstado(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="historial")
    estado_anterior = models.CharField(max_length=12, choices=Pedido.Estado)
    estado_nuevo = models.CharField(max_length=12, choices=Pedido.Estado)
    usuario_id = models.PositiveIntegerField(null=True, blank=True)
    comentario = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha", "id"]
        verbose_name_plural = "historial de estados"
