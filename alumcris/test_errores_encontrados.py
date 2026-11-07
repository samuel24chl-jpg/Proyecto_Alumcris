"""Errores (bugs) encontrados al escribir las pruebas.

Cada prueba describe cómo DEBERÍA comportarse el sitio. Hoy fallan porque el
error existe, así que están marcadas con @expectedFailure ("falla esperada"):
la suite sigue en verde y el error queda documentado y reproducible.

Cuando se corrija un error, su prueba empezará a pasar y Django lo informará
como "unexpected success" (éxito inesperado). En ese momento hay que quitarle
el @expectedFailure para que quede como una prueba normal.
"""

from unittest import expectedFailure

from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.urls import reverse

from cotizaciones.models import Cotizacion
from cotizaciones.test_cotizaciones import datos_de_cotizacion
from cotizaciones.tests import crear_cotizacion
from productos.models import Producto
from productos.test_productos import datos_de_producto
from productos.tests import crear_producto
from trabajos.tests import PruebaConMedios, imagen_de_prueba


class ErroresEnLasCotizacionesTests(PruebaConMedios):
    def setUp(self):
        self.producto = crear_producto()
        self.url = reverse("crear_cotizacion")

    @expectedFailure
    def test_bug_01_el_telefono_no_acepta_letras(self):
        """El filtro que deja solo números existe únicamente en el navegador
        (atributo oninput en cotizaciones/forms.py). El servidor no lo repite,
        así que una solicitud enviada sin ese filtro guarda letras."""
        self.client.post(
            self.url, datos_de_cotizacion(self.producto, telefono="abcdefghi")
        )

        self.assertFalse(Cotizacion.objects.exists())

    @expectedFailure
    def test_bug_02_el_nombre_del_cliente_no_acepta_numeros(self):
        """Misma causa que el bug 01, en el nombre del cliente."""
        self.client.post(
            self.url, datos_de_cotizacion(self.producto, nombre_cliente="Ana 123")
        )

        self.assertFalse(Cotizacion.objects.exists())

    @expectedFailure
    def test_bug_03_medidas_enormes_no_provocan_un_error_del_servidor(self):
        """El formulario acepta medidas de hasta 99.999 cm y no limita la
        cantidad. 99.999 × 99.999 cm × 20.000 unidades dan unos 20 mil millones
        de m², más de lo que cabe en superficie_total (máximo 9.999.999.999,99).
        MySQL rechaza el valor (DataError) y el sitio responde con un error 500
        en vez de mostrar un mensaje en el formulario."""
        datos = datos_de_cotizacion(
            self.producto, ancho="99999", alto="99999", cantidad="20000"
        )

        respuesta = self.client.post(self.url, datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Cotizacion.objects.exists())

    @expectedFailure
    def test_bug_04_se_puede_editar_una_cotizacion_de_un_producto_no_publicado(self):
        """El formulario de cotización solo ofrece productos publicados
        (CotizacionForm.producto) y el panel lo reutiliza para editar. Si un
        producto se despublica, sus cotizaciones ya no se pueden modificar."""
        self.client.force_login(User.objects.create_user("admin", is_staff=True))
        cotizacion = crear_cotizacion(self.producto)
        Producto.objects.filter(id=self.producto.id).update(publicado=False)

        respuesta = self.client.post(
            reverse("editar_cotizacion", args=[cotizacion.id]),
            datos_de_cotizacion(self.producto, telefono="987654321"),
        )

        self.assertRedirects(respuesta, reverse("panel_cotizaciones"))


class ErroresEnLosProductosTests(PruebaConMedios):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser("admin"))

    @expectedFailure
    def test_bug_05_el_nombre_del_producto_no_acepta_numeros(self):
        """Misma causa que los bugs 01 y 02: el nombre del producto se filtra
        solo en el navegador (productos/forms.py)."""
        datos = datos_de_producto(nombre="Ventana 2000", imagen=imagen_de_prueba())

        self.client.post(reverse("crear_producto"), datos)

        self.assertFalse(Producto.objects.exists())

    @expectedFailure
    def test_bug_06_reemplazar_la_imagen_borra_el_archivo_anterior(self):
        """Producto.delete() borra la imagen al eliminar el producto, pero al
        cambiarla por otra desde el panel el archivo anterior queda en disco."""
        producto = crear_producto(imagen=imagen_de_prueba("anterior.jpg"))
        anterior = producto.imagen.name

        self.client.post(
            reverse("editar_producto", args=[producto.id]),
            datos_de_producto(imagen=imagen_de_prueba("nueva.jpg")),
        )

        self.assertFalse(default_storage.exists(anterior))

    @expectedFailure
    def test_bug_07_el_borrado_masivo_del_admin_borra_las_imagenes(self):
        """La acción "Eliminar productos seleccionados" del admin de Django
        borra en lote y no llama a Producto.delete(), así que las imágenes
        quedan en disco. trabajos/models.py evita lo mismo con una señal."""
        producto = crear_producto(imagen=imagen_de_prueba("masivo.jpg"))
        imagen = producto.imagen.name

        self.client.post(
            "/admin/productos/producto/",
            {
                "action": "delete_selected",
                "_selected_action": [producto.id],
                "post": "yes",
            },
        )

        self.assertFalse(Producto.objects.exists())
        self.assertFalse(default_storage.exists(imagen))
