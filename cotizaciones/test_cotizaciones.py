"""Pruebas de la solicitud de cotizaciones y de su gestión en el panel.

Complementan las de cotizaciones/tests.py sin modificarlo.
"""

from datetime import UTC, datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from productos.tests import crear_producto

from .models import Cotizacion
from .tests import crear_cotizacion


def datos_de_cotizacion(producto, **cambios):
    """Datos válidos para enviar el formulario de cotización."""
    datos = {
        "producto": producto.id,
        "nombre_cliente": "Ana Pérez",
        "telefono": "912345678",
        "ancho": "200",
        "alto": "150",
        "cantidad": "2",
    }
    datos.update(cambios)
    return datos


class SolicitudDeCotizacionTests(TestCase):
    def setUp(self):
        self.producto = crear_producto()
        self.url = reverse("crear_cotizacion")

    def test_no_requiere_iniciar_sesion(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_guarda_la_solicitud_y_muestra_la_pagina_de_exito(self):
        respuesta = self.client.post(self.url, datos_de_cotizacion(self.producto))

        self.assertRedirects(respuesta, reverse("cotizacion_exito"))
        cotizacion = Cotizacion.objects.get()
        self.assertEqual(cotizacion.producto, self.producto)
        self.assertEqual(cotizacion.nombre_cliente, "Ana Pérez")
        self.assertEqual(cotizacion.telefono, "912345678")

    def test_la_solicitud_queda_pendiente_de_revision(self):
        self.client.post(self.url, datos_de_cotizacion(self.producto))

        self.assertEqual(Cotizacion.objects.get().estado, "Pendiente")

    def test_calcula_la_superficie_total_en_metros_cuadrados(self):
        # superficie = ancho (cm) × alto (cm) × cantidad / 10.000, con 2 decimales
        casos = [
            ("100", "100", "1", Decimal("1.00")),  # 1 m × 1 m
            ("200", "150", "2", Decimal("6.00")),  # 3 m² por unidad, 2 unidades
            ("50", "40", "1", Decimal("0.20")),  # menos de 1 m²
            ("123.45", "67.89", "3", Decimal("2.51")),  # 2,5143... se redondea
        ]
        for ancho, alto, cantidad, esperado in casos:
            with self.subTest(ancho=ancho, alto=alto, cantidad=cantidad):
                self.client.post(
                    self.url,
                    datos_de_cotizacion(
                        self.producto, ancho=ancho, alto=alto, cantidad=cantidad
                    ),
                )

                cotizacion = Cotizacion.objects.latest("id")
                self.assertEqual(cotizacion.superficie_total, esperado)

    def test_rechaza_datos_no_validos(self):
        # Partición de equivalencia y valores límite: cada caso rompe una sola regla.
        no_publicado = crear_producto(nombre="Ventana oculta", publicado=False)
        casos = {
            "nombre de 2 letras (mínimo 3)": {"nombre_cliente": "Al"},
            "teléfono de 8 dígitos": {"telefono": "12345678"},
            "teléfono de 10 dígitos": {"telefono": "1234567890"},
            "ancho menor a 1 cm": {"ancho": "0.99"},
            "alto negativo": {"alto": "-150"},
            "cantidad 0": {"cantidad": "0"},
            "cantidad con decimales": {"cantidad": "1.5"},
            "producto no publicado": {"producto": no_publicado.id},
            "producto que no existe": {"producto": 999999},
        }
        for caso, cambios in casos.items():
            with self.subTest(caso):
                datos = datos_de_cotizacion(self.producto)
                datos.update(cambios)

                respuesta = self.client.post(self.url, datos)

                self.assertEqual(respuesta.status_code, 200)
                self.assertFalse(Cotizacion.objects.exists())

    def test_acepta_los_valores_minimos_permitidos(self):
        # Valores límite: nombre de 3 letras y medidas y cantidad iguales a 1.
        datos = datos_de_cotizacion(
            self.producto, nombre_cliente="Ana", ancho="1", alto="1", cantidad="1"
        )

        respuesta = self.client.post(self.url, datos)

        self.assertRedirects(respuesta, reverse("cotizacion_exito"))


class ListadoDeCotizacionesTests(TestCase):
    def test_ordena_de_la_mas_reciente_a_la_mas_antigua(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))
        producto = crear_producto()
        fechas = {
            "marzo": datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            "enero": datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
            "mayo": datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
        }
        cotizaciones = {}
        for mes, fecha in fechas.items():
            cotizacion = crear_cotizacion(producto)
            # La fecha se completa sola al crear la cotización; se cambia después.
            Cotizacion.objects.filter(id=cotizacion.id).update(fecha_solicitud=fecha)
            cotizaciones[mes] = cotizacion

        respuesta = self.client.get(reverse("panel_cotizaciones"))

        self.assertEqual(
            list(respuesta.context["cotizaciones"]),
            [cotizaciones["mayo"], cotizaciones["marzo"], cotizaciones["enero"]],
        )


class EditarCotizacionTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))
        self.producto = crear_producto()
        self.cotizacion = crear_cotizacion(self.producto)
        self.url = reverse("editar_cotizacion", args=[self.cotizacion.id])

    def test_recalcula_la_superficie_al_guardar(self):
        datos = datos_de_cotizacion(self.producto, ancho="300", alto="200", cantidad="2")

        respuesta = self.client.post(self.url, datos)

        self.assertRedirects(respuesta, reverse("panel_cotizaciones"))
        self.cotizacion.refresh_from_db()
        self.assertEqual(self.cotizacion.superficie_total, Decimal("12.00"))

    def test_no_guarda_cambios_no_validos(self):
        respuesta = self.client.post(
            self.url, datos_de_cotizacion(self.producto, telefono="123")
        )

        self.assertEqual(respuesta.status_code, 200)
        self.cotizacion.refresh_from_db()
        self.assertEqual(self.cotizacion.telefono, "912345678")


class CambiarEstadoTests(TestCase):
    def test_rechaza_un_estado_que_no_existe(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))
        cotizacion = crear_cotizacion(crear_producto())

        self.client.post(
            reverse("cambiar_estado", args=[cotizacion.id]),
            {"estado": "Inventado"},
        )

        cotizacion.refresh_from_db()
        self.assertEqual(cotizacion.estado, "Pendiente")


class EliminarCotizacionTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))
        self.cotizacion = crear_cotizacion(crear_producto())
        self.url = reverse("eliminar_cotizacion", args=[self.cotizacion.id])

    def test_pide_confirmacion_antes_de_eliminar(self):
        respuesta = self.client.get(self.url)

        self.assertContains(respuesta, "Ana Pérez")
        self.assertTrue(Cotizacion.objects.filter(id=self.cotizacion.id).exists())

    def test_elimina_la_cotizacion_al_confirmar(self):
        respuesta = self.client.post(self.url)

        self.assertRedirects(respuesta, reverse("panel_cotizaciones"))
        self.assertFalse(Cotizacion.objects.filter(id=self.cotizacion.id).exists())


class AccesoAlPanelDeCotizacionesTests(TestCase):
    def setUp(self):
        self.cotizacion = crear_cotizacion(crear_producto())
        self.rutas = [
            reverse("panel_cotizaciones"),
            reverse("editar_cotizacion", args=[self.cotizacion.id]),
            reverse("cambiar_estado", args=[self.cotizacion.id]),
            reverse("eliminar_cotizacion", args=[self.cotizacion.id]),
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

    def test_un_visitante_no_puede_modificar_cotizaciones(self):
        self.client.post(
            reverse("cambiar_estado", args=[self.cotizacion.id]),
            {"estado": "Aprobada"},
        )
        self.client.post(reverse("eliminar_cotizacion", args=[self.cotizacion.id]))

        self.assertTrue(
            Cotizacion.objects.filter(id=self.cotizacion.id, estado="Pendiente").exists()
        )
