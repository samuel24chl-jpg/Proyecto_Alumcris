"""Pruebas del catálogo público y del panel de administración de productos.

Complementan las de productos/tests.py sin modificarlo.
"""

from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from trabajos.tests import PruebaConMedios, imagen_de_prueba

from .models import Producto
from .tests import crear_producto


def datos_de_producto(**cambios):
    """Datos válidos para enviar el formulario de un producto."""
    datos = {
        "nombre": "Ventana proyectante",
        "material": "PVC",
        "tipo": "Proyectante",
        "descripcion": "Ventana de PVC que se abre hacia afuera.",
        "publicado": "on",
    }
    datos.update(cambios)
    return datos


class CatalogoTests(TestCase):
    def test_muestra_solo_los_productos_publicados(self):
        crear_producto(nombre="Ventana visible")
        crear_producto(nombre="Ventana oculta", publicado=False)

        respuesta = self.client.get(reverse("catalogo"))

        self.assertContains(respuesta, "Ventana visible")
        self.assertNotContains(respuesta, "Ventana oculta")


class ProductosDelInicioTests(TestCase):
    def test_muestra_como_maximo_tres_productos(self):
        for numero in range(4):
            crear_producto(nombre=f"Ventana {numero}")

        respuesta = self.client.get(reverse("inicio"))

        self.assertEqual(len(respuesta.context["productos"]), 3)

    def test_no_muestra_productos_no_publicados(self):
        crear_producto(nombre="Ventana oculta", publicado=False)

        respuesta = self.client.get(reverse("inicio"))

        self.assertNotContains(respuesta, "Ventana oculta")


class ListadoDelPanelTests(TestCase):
    def test_incluye_los_productos_no_publicados(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))
        crear_producto(nombre="Ventana oculta", publicado=False)

        respuesta = self.client.get(reverse("panel"))

        self.assertContains(respuesta, "Ventana oculta")


class CrearProductoTests(PruebaConMedios):
    def setUp(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))
        self.url = reverse("crear_producto")

    def test_guarda_el_producto_y_vuelve_al_panel(self):
        datos = datos_de_producto(imagen=imagen_de_prueba("proyectante.jpg"))

        respuesta = self.client.post(self.url, datos)

        self.assertRedirects(respuesta, reverse("panel"))
        producto = Producto.objects.get()
        self.assertEqual(producto.nombre, "Ventana proyectante")
        self.assertEqual(producto.material, "PVC")
        self.assertTrue(default_storage.exists(producto.imagen.name))

    def test_rechaza_datos_no_validos(self):
        # Partición de equivalencia y valores límite: cada caso rompe una sola regla.
        casos = {
            "nombre de 2 letras (mínimo 3)": {"nombre": "Ve"},
            "descripción de 9 caracteres (mínimo 10)": {"descripcion": "Muy corta"},
            "material fuera de la lista": {"material": "Madera"},
            "tipo fuera de la lista": {"tipo": "Ventanal"},
        }
        for caso, cambios in casos.items():
            with self.subTest(caso):
                datos = datos_de_producto(imagen=imagen_de_prueba(), **cambios)

                respuesta = self.client.post(self.url, datos)

                self.assertEqual(respuesta.status_code, 200)
                self.assertFalse(Producto.objects.exists())

    def test_acepta_los_valores_minimos_permitidos(self):
        # Valores límite: nombre de 3 letras y descripción de 10 caracteres.
        datos = datos_de_producto(
            nombre="PVC",
            descripcion="Ventana XL",
            imagen=imagen_de_prueba(),
        )

        respuesta = self.client.post(self.url, datos)

        self.assertRedirects(respuesta, reverse("panel"))
        self.assertTrue(Producto.objects.filter(nombre="PVC").exists())

    def test_exige_una_imagen(self):
        respuesta = self.client.post(self.url, datos_de_producto())

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Producto.objects.exists())

    def test_rechaza_un_archivo_que_no_es_imagen(self):
        # Se revisa el contenido del archivo, no solo su extensión.
        archivo = SimpleUploadedFile("ventana.jpg", b"no soy una imagen")

        respuesta = self.client.post(self.url, datos_de_producto(imagen=archivo))

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Producto.objects.exists())


class EditarProductoTests(PruebaConMedios):
    def setUp(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))

    def url(self, producto):
        return reverse("editar_producto", args=[producto.id])

    def test_guarda_los_cambios_y_vuelve_al_panel(self):
        producto = crear_producto()

        respuesta = self.client.post(
            self.url(producto),
            datos_de_producto(nombre="Ventana fija", tipo="Fija"),
        )

        self.assertRedirects(respuesta, reverse("panel"))
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, "Ventana fija")
        self.assertEqual(producto.tipo, "Fija")

    def test_sin_imagen_nueva_conserva_la_actual(self):
        producto = crear_producto(imagen="imagenes/actual.jpg")

        self.client.post(self.url(producto), datos_de_producto())

        producto.refresh_from_db()
        self.assertEqual(producto.imagen.name, "imagenes/actual.jpg")

    def test_con_imagen_nueva_la_reemplaza(self):
        producto = crear_producto()

        self.client.post(
            self.url(producto),
            datos_de_producto(imagen=imagen_de_prueba("nueva.jpg")),
        )

        producto.refresh_from_db()
        self.assertTrue(producto.imagen.name.startswith("imagenes/nueva"))
        self.assertTrue(default_storage.exists(producto.imagen.name))

    def test_no_guarda_cambios_no_validos(self):
        producto = crear_producto(nombre="Ventana corredera")

        respuesta = self.client.post(self.url(producto), datos_de_producto(nombre="Ve"))

        self.assertEqual(respuesta.status_code, 200)
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, "Ventana corredera")


class EliminarProductoTests(PruebaConMedios):
    def setUp(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))

    def url(self, producto):
        return reverse("eliminar_producto", args=[producto.id])

    def test_pide_confirmacion_antes_de_eliminar(self):
        producto = crear_producto(nombre="Ventana fija")

        respuesta = self.client.get(self.url(producto))

        self.assertContains(respuesta, "Ventana fija")
        self.assertTrue(Producto.objects.filter(id=producto.id).exists())

    def test_elimina_el_producto_al_confirmar(self):
        producto = crear_producto()

        respuesta = self.client.post(self.url(producto))

        self.assertRedirects(respuesta, reverse("panel"))
        self.assertFalse(Producto.objects.filter(id=producto.id).exists())

    def test_al_eliminar_el_producto_se_borra_su_imagen(self):
        producto = crear_producto(imagen=imagen_de_prueba("borrar.jpg"))
        imagen = producto.imagen.name
        self.assertTrue(default_storage.exists(imagen))

        self.client.post(self.url(producto))

        self.assertFalse(default_storage.exists(imagen))


class AccesoAlPanelDeProductosTests(PruebaConMedios):
    def setUp(self):
        self.producto = crear_producto()
        self.rutas = [
            reverse("panel"),
            reverse("crear_producto"),
            reverse("editar_producto", args=[self.producto.id]),
            reverse("eliminar_producto", args=[self.producto.id]),
        ]

    def test_redirige_a_los_visitantes_al_inicio_de_sesion(self):
        for ruta in self.rutas:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)

                self.assertRedirects(
                    respuesta,
                    f"/ingresar/?next={ruta}",
                    fetch_redirect_response=False,
                )

    def test_rechaza_a_usuarios_que_no_son_administradores(self):
        self.client.force_login(User.objects.create_user("cliente"))

        for ruta in self.rutas:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 403)

    def test_un_visitante_no_puede_eliminar_productos(self):
        self.client.post(reverse("eliminar_producto", args=[self.producto.id]))

        self.assertTrue(Producto.objects.filter(id=self.producto.id).exists())
