from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

from productos.opciones import MATERIALES, TIPOS

from .imagenes import optimizar_imagen


class TrabajoQuerySet(models.QuerySet):
    def visibles(self):
        """Trabajos que se pueden mostrar en el sitio público."""
        return self.filter(publicado=True, fotos__isnull=False).distinct()


class Trabajo(models.Model):
    titulo = models.CharField(max_length=120, verbose_name="Título")
    descripcion = models.TextField(verbose_name="Descripción")
    material = models.CharField(
        max_length=50, choices=MATERIALES, verbose_name="Material"
    )
    tipo = models.CharField(max_length=50, choices=TIPOS, verbose_name="Tipo")
    comuna = models.CharField(max_length=80, verbose_name="Comuna")
    fecha = models.DateField(
        default=timezone.localdate, verbose_name="Fecha de término"
    )
    producto = models.ForeignKey(
        "productos.Producto",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trabajos",
        verbose_name="Producto relacionado",
    )
    destacado = models.BooleanField(
        default=False, verbose_name="Destacado en el inicio"
    )
    publicado = models.BooleanField(default=True, verbose_name="Publicado")

    objects = TrabajoQuerySet.as_manager()

    class Meta:
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return self.titulo

    @property
    def portada(self):
        fotos = self.fotos.all()
        return fotos[0] if fotos else None


class FotoTrabajo(models.Model):
    trabajo = models.ForeignKey(
        Trabajo,
        on_delete=models.CASCADE,
        related_name="fotos",
        verbose_name="Trabajo",
    )
    imagen = models.ImageField(upload_to="trabajos/", verbose_name="Imagen")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering = ["orden", "id"]
        verbose_name = "foto"
        verbose_name_plural = "fotos"

    def __str__(self):
        return f"Foto {self.orden} de {self.trabajo}"

    def save(self, *args, **kwargs):
        # Solo se procesan los archivos recién subidos, no los ya guardados.
        if self.imagen and not self.imagen._committed:
            self.imagen = optimizar_imagen(self.imagen)

        super().save(*args, **kwargs)


# Una señal también cubre los borrados en cascada, que no llaman a delete().
@receiver(post_delete, sender=FotoTrabajo)
def borrar_archivo_de_foto(sender, instance, **kwargs):
    instance.imagen.delete(save=False)
