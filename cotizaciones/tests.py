from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from productos.tests import crear_producto, etiqueta_del_campo

from .models import Cotizacion


def crear_cotizacion(producto):
    return Cotizacion.objects.create(
        producto=producto,
        nombre_cliente="Ana Pérez",
        telefono="912345678",
        ancho=100,
        alto=100,
        cantidad=1,
    )


class FormularioDeCotizacionTests(TestCase):
    def setUp(self):
        self.url = reverse("crear_cotizacion")

    def test_usa_los_estilos_de_bootstrap(self):
        respuesta = self.client.get(self.url)

        esperados = {
            "producto": "form-select",
            "nombre_cliente": "form-control",
            "telefono": "form-control",
            "ancho": "form-control",
            "alto": "form-control",
            "cantidad": "form-control",
        }
        for campo, clase in esperados.items():
            with self.subTest(campo=campo):
                self.assertIn(clase, etiqueta_del_campo(respuesta, campo))

    def test_conserva_los_filtros_de_nombre_y_telefono(self):
        respuesta = self.client.get(self.url)

        self.assertIn("oninput", etiqueta_del_campo(respuesta, "nombre_cliente"))
        self.assertIn("oninput", etiqueta_del_campo(respuesta, "telefono"))

    def test_la_opcion_vacia_del_producto_esta_en_espanol(self):
        respuesta = self.client.get(self.url)

        self.assertNotContains(respuesta, "Select an option")
        self.assertContains(respuesta, "Selecciona un producto")

    def test_preselecciona_el_producto_indicado_en_la_url(self):
        producto = crear_producto()

        respuesta = self.client.get(self.url, {"producto": producto.id})

        self.assertContains(
            respuesta,
            f'<option value="{producto.id}" selected>{producto.nombre}</option>',
            html=True,
        )


class PanelDeCotizacionesTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))

    def test_las_rutas_responden_404_si_la_cotizacion_no_existe(self):
        for nombre in ["editar_cotizacion", "cambiar_estado", "eliminar_cotizacion"]:
            with self.subTest(ruta=nombre):
                respuesta = self.client.get(reverse(nombre, args=[999]))

                self.assertEqual(respuesta.status_code, 404)

    def test_el_formulario_de_estado_usa_los_estilos_de_bootstrap(self):
        cotizacion = crear_cotizacion(crear_producto())

        respuesta = self.client.get(reverse("cambiar_estado", args=[cotizacion.id]))

        self.assertIn("form-select", etiqueta_del_campo(respuesta, "estado"))

    def test_cambiar_estado_sigue_guardando(self):
        cotizacion = crear_cotizacion(crear_producto())

        self.client.post(
            reverse("cambiar_estado", args=[cotizacion.id]),
            {"estado": "Aprobada"},
        )

        cotizacion.refresh_from_db()
        self.assertEqual(cotizacion.estado, "Aprobada")
