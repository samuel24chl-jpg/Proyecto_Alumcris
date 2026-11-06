from django.db import models

# Create your models here.
class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    material = models.CharField(max_length=50, verbose_name='Material')
    tipo = models.CharField(max_length=50, verbose_name='Tipo')
    descripcion = models.TextField(verbose_name='Descripción')
    imagen = models.ImageField(upload_to='imagenes/',verbose_name='Imagen')
    publicado = models.BooleanField(default=True, verbose_name='Publicado')

    def __str__(self):
        return self.nombre

    def delete(self, using=None, keep_parents=False):
        self.imagen.storage.delete(self.imagen.name)
        super().delete()