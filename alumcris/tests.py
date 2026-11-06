import re
from datetime import UTC, date, datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cotizaciones.tests import crear_cotizacion
from productos.tests import crear_producto


class FaviconTests(TestCase):
    def test_todas_las_paginas_enlazan_iconos_que_existen(self):
        html = self.client.get(reverse("inicio")).content.decode()

        enlaces = re.findall(r'<link[^>]*rel="icon"[^>]*href="([^"]+)"', html)

        self.assertTrue(enlaces, "La plantilla base no declara ningún icono")
        for enlace in enlaces:
            with self.subTest(enlace=enlace):
                ruta = enlace.split(settings.STATIC_URL, 1)[1]
                self.assertIsNotNone(finders.find(ruta))

    def test_la_ruta_clasica_del_favicon_lleva_al_icono(self):
        # El admin de Django y otras páginas sin base.html piden esta ruta.
        respuesta = self.client.get("/favicon.ico")

        self.assertRedirects(
            respuesta,
            "/static/favicon.png",
            fetch_redirect_response=False,
        )


class AdminDeDjangoTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser("admin"))

    def test_los_selectores_estan_en_espanol(self):
        rutas = [
            "/admin/trabajos/trabajo/add/",
            "/admin/cotizaciones/cotizacion/add/",
        ]
        for ruta in rutas:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(ruta)

                self.assertNotContains(respuesta, "Select an option")
                self.assertContains(respuesta, "Seleccione una opción")

    def test_el_boton_de_acciones_esta_en_espanol(self):
        crear_producto()

        respuesta = self.client.get("/admin/productos/producto/")

        self.assertNotContains(respuesta, ">Run</button>")
        self.assertContains(respuesta, ">Ejecutar</button>")

    def test_la_confirmacion_de_borrado_esta_en_espanol(self):
        producto = crear_producto(nombre="Ventana fija")

        respuesta = self.client.get(f"/admin/productos/producto/{producto.id}/delete/")

        self.assertNotContains(respuesta, "Are you sure")
        self.assertContains(respuesta, "¿Está seguro de que quiere borrar")
        self.assertContains(respuesta, "Ventana fija")

    def test_el_plural_de_cotizacion_no_tiene_errores(self):
        respuesta = self.client.get("/admin/")

        self.assertNotContains(respuesta, "Cotizacions")

    def test_las_fotos_de_un_trabajo_tienen_un_titulo_claro(self):
        respuesta = self.client.get("/admin/trabajos/trabajo/add/")

        self.assertNotContains(respuesta, "Foto trabajo")
        self.assertContains(respuesta, "Fotos")

    def test_el_listado_de_productos_muestra_sus_columnas(self):
        crear_producto()

        respuesta = self.client.get("/admin/productos/producto/")

        for columna in ["nombre", "material", "tipo", "imagen", "publicado"]:
            with self.subTest(columna=columna):
                self.assertContains(respuesta, f"column-{columna}")

    def test_el_listado_de_cotizaciones_muestra_sus_columnas(self):
        crear_cotizacion(crear_producto())

        respuesta = self.client.get("/admin/cotizaciones/cotizacion/")

        columnas = [
            "nombre_cliente",
            "producto",
            "superficie_total",
            "estado",
            "fecha_solicitud",
        ]
        for columna in columnas:
            with self.subTest(columna=columna):
                self.assertContains(respuesta, f"column-{columna}")


class ZonaHorariaTests(TestCase):
    def test_las_fechas_se_calculan_con_la_hora_de_chile(self):
        # A la 01:00 UTC del 4 de noviembre, en Chile aún es 3 de noviembre.
        instante = datetime(2026, 11, 4, 1, 0, tzinfo=UTC)

        self.assertEqual(timezone.localdate(instante), date(2026, 11, 3))


class MenuDeAdministracionTests(TestCase):
    def test_agrupa_los_enlaces_de_administracion_en_un_desplegable(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))

        html = self.client.get(reverse("inicio")).content.decode()

        desplegable = re.search(r'<ul class="dropdown-menu.*?</ul>', html, re.DOTALL)
        self.assertIsNotNone(desplegable, "El menú no tiene un desplegable")
        for ruta in ["/panel/", "/cotizaciones/panel/", "/panel/trabajos/"]:
            with self.subTest(ruta=ruta):
                self.assertIn(f'href="{ruta}"', desplegable.group())

    def test_un_visitante_no_ve_el_desplegable(self):
        respuesta = self.client.get(reverse("inicio"))

        self.assertNotContains(respuesta, 'data-bs-toggle="dropdown"')
