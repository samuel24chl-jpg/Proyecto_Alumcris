"""Pruebas del inicio de sesión del panel de administración."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

CLAVE = "clave-de-prueba-123"


class InicioDeSesionTests(TestCase):
    def setUp(self):
        self.url = reverse("ingresar")

    def test_un_administrador_ingresa_y_llega_al_panel(self):
        User.objects.create_user("admin", password=CLAVE, is_staff=True)

        respuesta = self.client.post(
            self.url, {"username": "admin", "password": CLAVE}
        )

        self.assertRedirects(respuesta, reverse("panel"))

    def test_un_usuario_que_no_es_administrador_no_puede_ingresar(self):
        User.objects.create_user("cliente", password=CLAVE)

        respuesta = self.client.post(
            self.url, {"username": "cliente", "password": CLAVE}
        )

        self.assertContains(respuesta, "No fue posible ingresar")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_despues_de_ingresar_vuelve_a_la_pagina_que_pidio(self):
        User.objects.create_user("admin", password=CLAVE, is_staff=True)
        destino = reverse("panel_cotizaciones")

        # 1. Un visitante pide una página protegida y lo envían a ingresar.
        respuesta = self.client.get(destino)
        self.assertRedirects(respuesta, f"{self.url}?next={destino}")

        # 2. El formulario de ingreso recuerda la página que pidió.
        formulario = self.client.get(respuesta.url)
        self.assertContains(formulario, f'name="next" value="{destino}"')

        # 3. Al ingresar, vuelve a esa página.
        respuesta = self.client.post(
            self.url, {"username": "admin", "password": CLAVE, "next": destino}
        )
        self.assertRedirects(respuesta, destino)
