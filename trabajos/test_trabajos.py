"""Pruebas de cómo se muestran los trabajos y sus fotos en el admin de Django.

Complementan las de trabajos/tests.py sin modificarlo.
"""

from django.contrib.auth.models import User

from .tests import PruebaConMedios, crear_trabajo


class NombresEnElAdminTests(PruebaConMedios):
    def test_la_confirmacion_de_borrado_nombra_el_trabajo_y_sus_fotos(self):
        self.client.force_login(User.objects.create_superuser("admin"))
        trabajo = crear_trabajo(titulo="Ventanas en Maipú", fotos=1)

        respuesta = self.client.get(f"/admin/trabajos/trabajo/{trabajo.id}/delete/")

        self.assertContains(respuesta, "Ventanas en Maipú")
        self.assertContains(respuesta, "Foto 0 de Ventanas en Maipú")
        # Sin un nombre propio, Django mostraría "Trabajo object (1)".
        self.assertNotContains(respuesta, "object (")
