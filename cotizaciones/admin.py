from django.contrib import admin
from .models import Cotizacion

# Register your models here.
@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_cliente', 'producto', 'superficie_total', 'estado', 'fecha_solicitud']
