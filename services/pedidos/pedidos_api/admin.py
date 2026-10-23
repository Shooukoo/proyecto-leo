from django.contrib import admin

from .models import Cliente, Direccion, HistorialEstado, Pedido

admin.site.register([Cliente, Direccion, Pedido, HistorialEstado])
