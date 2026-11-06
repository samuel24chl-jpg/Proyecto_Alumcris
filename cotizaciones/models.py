from django.db import models

# Create your models here.
class Cotizacion(models.Model):
    producto = models.ForeignKey('productos.Producto',on_delete=models.CASCADE,verbose_name='Producto solicitado')
    nombre_cliente = models.CharField(max_length=100,verbose_name='Nombre del cliente')
    telefono = models.CharField(max_length=20,verbose_name='Teléfono')
    ancho = models.DecimalField(max_digits=7,decimal_places=2,verbose_name='Ancho (cm)')
    alto = models.DecimalField(max_digits=7,decimal_places=2,verbose_name='Alto (cm)')
    cantidad = models.PositiveIntegerField(verbose_name='Cantidad')
    superficie_total = models.DecimalField(max_digits=12,decimal_places=2,default=0,verbose_name='Total')
    estado = models.CharField(max_length=20,default='Pendiente',verbose_name='Estado')
    fecha_solicitud = models.DateTimeField(auto_now_add=True,verbose_name='Fecha')

    class Meta:
        verbose_name = 'cotización'
        verbose_name_plural = 'cotizaciones'

    def __str__(self):
        return self.nombre_cliente
