import re

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Producto


def crear_producto(**datos):
    valores = {
        "nombre": "Ventana corredera",
        "material": "Aluminio",
        "tipo": "Corredera",
        "descripcion": "Ventana de prueba.",
        "imagen": "imagenes/prueba.jpg",
    }
    valores.update(datos)
    return Producto.objects.create(**valores)


def etiqueta_del_campo(respuesta, nombre):
    """Devuelve la etiqueta HTML con la que se muestra un campo del formulario."""
    coincidencia = re.search(
        rf'<(?:input|select|textarea)[^>]*name="{nombre}"[^>]*>',
        respuesta.content.decode(),
    )
    return coincidencia.group() if coincidencia else ""


class DetalleDeProductoTests(TestCase):
    def url(self, identificador):
        return reverse("detalle_producto", args=[identificador])

    def test_muestra_un_producto_publicado(self):
        producto = crear_producto(nombre="Ventana fija")

        respuesta = self.client.get(self.url(producto.id))

        self.assertContains(respuesta, "Ventana fija")

    def test_responde_404_si_no_existe(self):
        self.assertEqual(self.client.get(self.url(999)).status_code, 404)

    def test_responde_404_si_no_esta_publicado(self):
        producto = crear_producto(publicado=False)

        self.assertEqual(self.client.get(self.url(producto.id)).status_code, 404)


class PanelDeProductosTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))

    def test_las_rutas_responden_404_si_el_producto_no_existe(self):
        for nombre in ["editar_producto", "eliminar_producto"]:
            with self.subTest(ruta=nombre):
                respuesta = self.client.get(reverse(nombre, args=[999]))

                self.assertEqual(respuesta.status_code, 404)

    def test_editar_permite_gestionar_productos_no_publicados(self):
        producto = crear_producto(publicado=False)

        respuesta = self.client.get(reverse("editar_producto", args=[producto.id]))

        self.assertEqual(respuesta.status_code, 200)

    def test_el_formulario_usa_los_estilos_de_bootstrap(self):
        respuesta = self.client.get(reverse("crear_producto"))

        esperados = {
            "nombre": "form-control",
            "material": "form-select",
            "tipo": "form-select",
            "descripcion": "form-control",
            "imagen": "form-control",
            "publicado": "form-check-input",
        }
        for campo, clase in esperados.items():
            with self.subTest(campo=campo):
                self.assertIn(clase, etiqueta_del_campo(respuesta, campo))

    def test_el_nombre_conserva_su_filtro_de_caracteres(self):
        respuesta = self.client.get(reverse("crear_producto"))

        self.assertIn("oninput", etiqueta_del_campo(respuesta, "nombre"))
