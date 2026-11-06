import shutil
import tempfile
from datetime import date
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from productos.models import Producto
from productos.tests import etiqueta_del_campo

from .models import FotoTrabajo, Trabajo

ETIQUETA_GPS = 0x8825


def imagen_de_prueba(nombre="foto.jpg", tamano=(40, 30), exif=None):
    """Genera una imagen real en memoria para simular una subida."""
    salida = BytesIO()
    opciones = {"exif": exif} if exif else {}
    Image.new("RGB", tamano, "steelblue").save(salida, "JPEG", **opciones)
    return SimpleUploadedFile(nombre, salida.getvalue(), content_type="image/jpeg")


def crear_trabajo(fotos=1, **datos):
    """Crea un trabajo válido con la cantidad de fotos indicada."""
    valores = {
        "titulo": "Ventanas de aluminio",
        "descripcion": "Instalación completa en un departamento.",
        "material": "Aluminio",
        "tipo": "Corredera",
        "comuna": "Maipú",
        "fecha": date(2026, 10, 1),
    }
    valores.update(datos)
    trabajo = Trabajo.objects.create(**valores)
    for orden in range(fotos):
        FotoTrabajo.objects.create(
            trabajo=trabajo,
            imagen=imagen_de_prueba(f"foto{orden}.jpg"),
            orden=orden,
        )
    return trabajo


class PruebaConMedios(TestCase):
    """Guarda los archivos subidos en una carpeta temporal, nunca en imagenes/."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carpeta_medios = tempfile.mkdtemp()
        cls.ajuste_medios = override_settings(MEDIA_ROOT=cls.carpeta_medios)
        cls.ajuste_medios.enable()

    @classmethod
    def tearDownClass(cls):
        cls.ajuste_medios.disable()
        shutil.rmtree(cls.carpeta_medios, ignore_errors=True)
        super().tearDownClass()


class VisibilidadDeTrabajosTests(PruebaConMedios):
    def test_incluye_trabajo_publicado_con_foto(self):
        trabajo = crear_trabajo()

        self.assertEqual(list(Trabajo.objects.visibles()), [trabajo])

    def test_excluye_trabajo_no_publicado(self):
        crear_trabajo(publicado=False)

        self.assertEqual(list(Trabajo.objects.visibles()), [])

    def test_excluye_trabajo_sin_fotos(self):
        crear_trabajo(fotos=0)

        self.assertEqual(list(Trabajo.objects.visibles()), [])

    def test_no_repite_trabajo_con_varias_fotos(self):
        crear_trabajo(fotos=3)

        self.assertEqual(Trabajo.objects.visibles().count(), 1)

    def test_ordena_del_mas_reciente_al_mas_antiguo(self):
        antiguo = crear_trabajo(titulo="Antiguo", fecha=date(2025, 1, 1))
        reciente = crear_trabajo(titulo="Reciente", fecha=date(2026, 6, 1))

        self.assertEqual(list(Trabajo.objects.visibles()), [reciente, antiguo])


class PortadaTests(PruebaConMedios):
    def test_portada_es_la_foto_de_menor_orden(self):
        trabajo = crear_trabajo(fotos=0)
        segunda = FotoTrabajo.objects.create(
            trabajo=trabajo, imagen=imagen_de_prueba("b.jpg"), orden=2
        )
        primera = FotoTrabajo.objects.create(
            trabajo=trabajo, imagen=imagen_de_prueba("a.jpg"), orden=1
        )

        self.assertEqual(trabajo.portada, primera)
        self.assertNotEqual(trabajo.portada, segunda)

    def test_portada_es_nula_sin_fotos(self):
        self.assertIsNone(crear_trabajo(fotos=0).portada)


class OptimizacionDeFotosTests(PruebaConMedios):
    def test_reduce_fotos_mas_grandes_que_el_limite(self):
        foto = FotoTrabajo.objects.create(
            trabajo=crear_trabajo(fotos=0),
            imagen=imagen_de_prueba(tamano=(4000, 2000)),
        )

        with Image.open(foto.imagen.path) as guardada:
            self.assertEqual(guardada.size, (1920, 960))

    def test_no_agranda_fotos_pequenas(self):
        foto = FotoTrabajo.objects.create(
            trabajo=crear_trabajo(fotos=0),
            imagen=imagen_de_prueba(tamano=(40, 30)),
        )

        with Image.open(foto.imagen.path) as guardada:
            self.assertEqual(guardada.size, (40, 30))

    def test_elimina_la_ubicacion_gps_de_la_foto(self):
        exif = Image.Exif()
        exif.get_ifd(ETIQUETA_GPS)[1] = "S"
        original = imagen_de_prueba(exif=exif.tobytes())
        with Image.open(BytesIO(original.read())) as abierta:
            self.assertTrue(abierta.getexif().get_ifd(ETIQUETA_GPS))
        original.seek(0)

        foto = FotoTrabajo.objects.create(
            trabajo=crear_trabajo(fotos=0), imagen=original
        )

        with Image.open(foto.imagen.path) as guardada:
            self.assertFalse(guardada.getexif().get_ifd(ETIQUETA_GPS))

    def test_guarda_las_fotos_en_formato_webp(self):
        foto = FotoTrabajo.objects.create(
            trabajo=crear_trabajo(fotos=0), imagen=imagen_de_prueba("casa.jpg")
        )

        self.assertTrue(foto.imagen.name.startswith("trabajos/casa"))
        self.assertTrue(foto.imagen.name.endswith(".webp"))

    def test_volver_a_guardar_no_reprocesa_la_foto(self):
        foto = FotoTrabajo.objects.create(
            trabajo=crear_trabajo(fotos=0), imagen=imagen_de_prueba()
        )
        nombre = foto.imagen.name

        foto.orden = 5
        foto.save()

        self.assertEqual(foto.imagen.name, nombre)


class BorradoDeArchivosTests(PruebaConMedios):
    def test_eliminar_una_foto_borra_su_archivo(self):
        trabajo = crear_trabajo()
        foto = trabajo.fotos.get()
        nombre = foto.imagen.name

        foto.delete()

        self.assertFalse(default_storage.exists(nombre))

    def test_eliminar_un_trabajo_borra_los_archivos_de_sus_fotos(self):
        trabajo = crear_trabajo(fotos=2)
        nombres = [foto.imagen.name for foto in trabajo.fotos.all()]

        trabajo.delete()

        for nombre in nombres:
            self.assertFalse(default_storage.exists(nombre))


class GaleriaTests(PruebaConMedios):
    def setUp(self):
        self.url = reverse("galeria")

    def test_muestra_solo_trabajos_visibles(self):
        crear_trabajo(titulo="Obra visible")
        crear_trabajo(titulo="Obra oculta", publicado=False)

        respuesta = self.client.get(self.url)

        self.assertContains(respuesta, "Obra visible")
        self.assertNotContains(respuesta, "Obra oculta")

    def test_filtra_por_material(self):
        crear_trabajo(titulo="Obra de PVC", material="PVC")
        crear_trabajo(titulo="Obra de aluminio", material="Aluminio")

        respuesta = self.client.get(self.url, {"material": "PVC"})

        self.assertContains(respuesta, "Obra de PVC")
        self.assertNotContains(respuesta, "Obra de aluminio")

    def test_filtra_por_tipo(self):
        crear_trabajo(titulo="Obra fija", tipo="Fija")
        crear_trabajo(titulo="Obra corredera", tipo="Corredera")

        respuesta = self.client.get(self.url, {"tipo": "Fija"})

        self.assertContains(respuesta, "Obra fija")
        self.assertNotContains(respuesta, "Obra corredera")

    def test_combina_los_filtros(self):
        crear_trabajo(titulo="Coincide", material="PVC", tipo="Fija")
        crear_trabajo(titulo="Otro tipo", material="PVC", tipo="Puerta")
        crear_trabajo(titulo="Otro material", material="Vidrio", tipo="Fija")

        respuesta = self.client.get(self.url, {"material": "PVC", "tipo": "Fija"})

        self.assertContains(respuesta, "Coincide")
        self.assertNotContains(respuesta, "Otro tipo")
        self.assertNotContains(respuesta, "Otro material")

    def test_ignora_un_filtro_no_valido(self):
        crear_trabajo(titulo="Obra existente")

        respuesta = self.client.get(self.url, {"material": "Madera"})

        self.assertContains(respuesta, "Obra existente")

    def test_mantiene_el_filtro_seleccionado(self):
        respuesta = self.client.get(self.url, {"material": "PVC"})

        self.assertContains(
            respuesta,
            '<option value="PVC" selected>PVC</option>',
            html=True,
        )

    def test_avisa_si_ningun_trabajo_coincide(self):
        crear_trabajo(material="PVC")

        respuesta = self.client.get(self.url, {"material": "Vidrio"})

        self.assertContains(respuesta, "No hay trabajos con estos filtros")

    def test_avisa_si_aun_no_hay_trabajos(self):
        respuesta = self.client.get(self.url)

        self.assertContains(respuesta, "Pronto publicaremos nuestros trabajos")

    def test_muestra_nueve_trabajos_por_pagina(self):
        for numero in range(10):
            crear_trabajo(titulo=f"Obra {numero}")

        primera = self.client.get(self.url)
        segunda = self.client.get(self.url, {"pagina": 2})

        self.assertEqual(len(primera.context["pagina"].object_list), 9)
        self.assertEqual(len(segunda.context["pagina"].object_list), 1)

    def test_la_paginacion_conserva_los_filtros(self):
        for numero in range(10):
            crear_trabajo(titulo=f"Obra {numero}", material="PVC")

        respuesta = self.client.get(self.url, {"material": "PVC"})

        self.assertContains(respuesta, "?material=PVC&amp;pagina=2")

    def test_una_pagina_no_valida_no_rompe_la_galeria(self):
        crear_trabajo(titulo="Obra existente")

        respuesta = self.client.get(self.url, {"pagina": "abc"})

        self.assertContains(respuesta, "Obra existente")

    def test_cada_tarjeta_enlaza_a_su_detalle(self):
        trabajo = crear_trabajo()

        respuesta = self.client.get(self.url)

        self.assertContains(respuesta, f'href="/trabajos/{trabajo.id}/"')


class DetalleDeTrabajoTests(PruebaConMedios):
    def url(self, identificador):
        return reverse("detalle_trabajo", args=[identificador])

    def crear_producto(self):
        return Producto.objects.create(
            nombre="Ventana corredera",
            material="Aluminio",
            tipo="Corredera",
            descripcion="Ventana de prueba.",
            imagen="imagenes/prueba.jpg",
        )

    def test_muestra_todas_las_fotos_y_los_datos(self):
        trabajo = crear_trabajo(fotos=2, titulo="Obra en Maipú", comuna="Maipú")

        respuesta = self.client.get(self.url(trabajo.id))

        self.assertContains(respuesta, "Obra en Maipú")
        self.assertContains(respuesta, "Maipú")
        for foto in trabajo.fotos.all():
            self.assertContains(respuesta, foto.imagen.url)

    def test_responde_404_si_no_existe(self):
        self.assertEqual(self.client.get(self.url(999)).status_code, 404)

    def test_responde_404_si_no_esta_publicado(self):
        trabajo = crear_trabajo(publicado=False)

        self.assertEqual(self.client.get(self.url(trabajo.id)).status_code, 404)

    def test_responde_404_si_no_tiene_fotos(self):
        trabajo = crear_trabajo(fotos=0)

        self.assertEqual(self.client.get(self.url(trabajo.id)).status_code, 404)

    def test_preselecciona_el_producto_relacionado_al_cotizar(self):
        producto = self.crear_producto()
        trabajo = crear_trabajo(producto=producto)

        respuesta = self.client.get(self.url(trabajo.id))

        self.assertContains(
            respuesta,
            f'href="/cotizaciones/crear/?producto={producto.id}"',
        )

    def test_enlaza_a_cotizar_sin_producto_si_no_tiene_relacionado(self):
        trabajo = crear_trabajo()

        respuesta = self.client.get(self.url(trabajo.id))

        self.assertContains(respuesta, "Solicitar una cotización similar")
        self.assertNotContains(respuesta, "?producto=")

    def test_eliminar_el_producto_conserva_el_trabajo(self):
        producto = self.crear_producto()
        trabajo = crear_trabajo(producto=producto)

        producto.delete()

        trabajo.refresh_from_db()
        self.assertIsNone(trabajo.producto)


class CarruselDeInicioTests(PruebaConMedios):
    def setUp(self):
        self.url = reverse("inicio")

    def test_muestra_los_trabajos_destacados_en_lugar_del_bloque_azul(self):
        crear_trabajo(titulo="Obra destacada", destacado=True)

        respuesta = self.client.get(self.url)

        self.assertContains(respuesta, "Obra destacada")
        self.assertContains(respuesta, 'id="carruselInicio"')
        self.assertNotContains(respuesta, "Bienvenidos a Alumcris")

    def test_mantiene_el_bloque_azul_si_no_hay_destacados(self):
        crear_trabajo(titulo="Obra normal")

        respuesta = self.client.get(self.url)

        self.assertContains(respuesta, "Bienvenidos a Alumcris")
        self.assertNotContains(respuesta, 'id="carruselInicio"')
        self.assertNotContains(respuesta, "Obra normal")

    def test_excluye_destacados_no_publicados(self):
        crear_trabajo(titulo="Obra oculta", destacado=True, publicado=False)

        respuesta = self.client.get(self.url)

        self.assertNotContains(respuesta, "Obra oculta")

    def test_muestra_solo_los_cinco_destacados_mas_recientes(self):
        crear_trabajo(titulo="Obra antigua", destacado=True, fecha=date(2020, 1, 1))
        for mes in range(1, 6):
            crear_trabajo(
                titulo=f"Obra reciente {mes}",
                destacado=True,
                fecha=date(2026, mes, 1),
            )

        respuesta = self.client.get(self.url)

        self.assertEqual(len(respuesta.context["destacados"]), 5)
        self.assertNotContains(respuesta, "Obra antigua")

    def test_el_carrusel_tiene_controles_con_varios_destacados(self):
        crear_trabajo(destacado=True)
        crear_trabajo(destacado=True)

        respuesta = self.client.get(self.url)

        self.assertContains(respuesta, 'data-bs-slide="next"')
        self.assertContains(respuesta, "data-carrusel-pausa")

    def test_un_solo_destacado_no_muestra_controles(self):
        crear_trabajo(destacado=True)

        respuesta = self.client.get(self.url)

        self.assertNotContains(respuesta, 'data-bs-slide="next"')
        self.assertNotContains(respuesta, "data-carrusel-pausa")

    def test_cada_diapositiva_enlaza_al_detalle_del_trabajo(self):
        trabajo = crear_trabajo(destacado=True)

        respuesta = self.client.get(self.url)

        self.assertContains(respuesta, f'href="/trabajos/{trabajo.id}/"')


class MenuPrincipalTests(TestCase):
    def test_enlaza_a_la_galeria_de_trabajos(self):
        respuesta = self.client.get(reverse("inicio"))

        self.assertContains(respuesta, 'href="/trabajos/"')

    def test_el_menu_publico_no_enlaza_al_panel_de_trabajos(self):
        respuesta = self.client.get(reverse("inicio"))

        self.assertNotContains(respuesta, 'href="/panel/trabajos/"')

    def test_el_menu_de_administrador_enlaza_al_panel_de_trabajos(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))

        respuesta = self.client.get(reverse("inicio"))

        self.assertContains(respuesta, 'href="/panel/trabajos/"')


def datos_de_formulario(**cambios):
    """Datos válidos para enviar el formulario de un trabajo."""
    datos = {
        "titulo": "Termopanel en Ñuñoa",
        "descripcion": "Cambio de ventanas en un edificio.",
        "material": "PVC",
        "tipo": "Termopanel",
        "comuna": "Ñuñoa",
        "fecha": "2026-10-15",
        "publicado": "on",
    }
    datos.update(cambios)
    return datos


class PruebaDePanel(PruebaConMedios):
    def setUp(self):
        self.client.force_login(User.objects.create_user("admin", is_staff=True))


class AccesoAlPanelTests(PruebaConMedios):
    def rutas(self):
        trabajo = crear_trabajo()
        foto = trabajo.fotos.get()
        return [
            reverse("panel_trabajos"),
            reverse("crear_trabajo"),
            reverse("editar_trabajo", args=[trabajo.id]),
            reverse("eliminar_trabajo", args=[trabajo.id]),
            reverse("eliminar_foto_trabajo", args=[foto.id]),
            reverse("portada_foto_trabajo", args=[foto.id]),
        ]

    def test_redirige_a_visitantes_al_inicio_de_sesion(self):
        for ruta in self.rutas():
            with self.subTest(ruta=ruta):
                respuesta = self.client.post(ruta)

                self.assertEqual(respuesta.status_code, 302)
                self.assertIn("/ingresar/", respuesta.url)

    def test_rechaza_a_usuarios_que_no_son_administradores(self):
        self.client.force_login(User.objects.create_user("cliente"))

        for ruta in self.rutas():
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.post(ruta).status_code, 403)

    def test_ningun_visitante_puede_modificar_datos(self):
        trabajo = crear_trabajo(fotos=2)
        foto = trabajo.fotos.first()

        self.client.post(reverse("eliminar_trabajo", args=[trabajo.id]))
        self.client.post(reverse("eliminar_foto_trabajo", args=[foto.id]))

        self.assertEqual(trabajo.fotos.count(), 2)


class ListadoDelPanelTests(PruebaDePanel):
    def test_incluye_trabajos_no_publicados_y_sin_fotos(self):
        crear_trabajo(titulo="Obra oculta", publicado=False)
        crear_trabajo(titulo="Obra sin fotos", fotos=0)

        respuesta = self.client.get(reverse("panel_trabajos"))

        self.assertContains(respuesta, "Obra oculta")
        self.assertContains(respuesta, "Obra sin fotos")


class CrearTrabajoTests(PruebaDePanel):
    def setUp(self):
        super().setUp()
        self.url = reverse("crear_trabajo")

    def test_crea_el_trabajo_con_todas_sus_fotos_en_orden(self):
        datos = datos_de_formulario(
            fotos=[imagen_de_prueba("primera.jpg"), imagen_de_prueba("segunda.jpg")]
        )

        respuesta = self.client.post(self.url, datos)

        self.assertRedirects(respuesta, reverse("panel_trabajos"))
        trabajo = Trabajo.objects.get()
        self.assertEqual(trabajo.titulo, "Termopanel en Ñuñoa")
        nombres = [foto.imagen.name for foto in trabajo.fotos.all()]
        self.assertEqual(len(nombres), 2)
        self.assertIn("primera", nombres[0])
        self.assertIn("segunda", nombres[1])

    def test_exige_al_menos_una_foto(self):
        respuesta = self.client.post(self.url, datos_de_formulario())

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Trabajo.objects.exists())
        self.assertContains(respuesta, "Debes subir al menos una foto")

    def test_rechaza_un_archivo_que_no_es_imagen(self):
        archivo = SimpleUploadedFile("nota.txt", b"no soy una imagen")

        respuesta = self.client.post(self.url, datos_de_formulario(fotos=[archivo]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Trabajo.objects.exists())
        self.assertFalse(FotoTrabajo.objects.exists())

    def test_rechaza_todo_si_una_de_las_fotos_no_es_valida(self):
        malo = SimpleUploadedFile("nota.txt", b"no soy una imagen")

        self.client.post(
            self.url,
            datos_de_formulario(fotos=[imagen_de_prueba(), malo]),
        )

        self.assertFalse(Trabajo.objects.exists())
        self.assertFalse(FotoTrabajo.objects.exists())

    def test_no_guarda_nada_si_falta_un_dato_obligatorio(self):
        datos = datos_de_formulario(titulo="", fotos=[imagen_de_prueba()])

        respuesta = self.client.post(self.url, datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(FotoTrabajo.objects.exists())

    def test_el_formulario_permite_elegir_varias_fotos(self):
        respuesta = self.client.get(self.url)

        self.assertContains(respuesta, 'enctype="multipart/form-data"')
        self.assertRegex(
            respuesta.content.decode(),
            r'<input[^>]*type="file"[^>]*multiple',
        )

    def test_el_formulario_usa_los_estilos_de_bootstrap(self):
        respuesta = self.client.get(self.url)

        esperados = {
            "titulo": "form-control",
            "material": "form-select",
            "descripcion": "form-control",
            "producto": "form-select",
            "destacado": "form-check-input",
            "fotos": "form-control",
        }
        for campo, clase in esperados.items():
            with self.subTest(campo=campo):
                self.assertIn(clase, etiqueta_del_campo(respuesta, campo))

    def test_las_opciones_vacias_de_los_selectores_estan_en_espanol(self):
        respuesta = self.client.get(self.url)

        self.assertNotContains(respuesta, "Select an option")
        self.assertContains(respuesta, "Selecciona un material")
        self.assertContains(respuesta, "Selecciona un tipo")
        self.assertContains(respuesta, "Sin producto relacionado")

    def test_guarda_el_trabajo_como_destacado(self):
        datos = datos_de_formulario(destacado="on", fotos=[imagen_de_prueba()])

        self.client.post(self.url, datos)

        self.assertTrue(Trabajo.objects.get().destacado)


class EditarTrabajoTests(PruebaDePanel):
    def url(self, trabajo):
        return reverse("editar_trabajo", args=[trabajo.id])

    def test_actualiza_los_datos_sin_perder_las_fotos(self):
        trabajo = crear_trabajo(fotos=2)

        respuesta = self.client.post(
            self.url(trabajo), datos_de_formulario(titulo="Título nuevo")
        )

        self.assertRedirects(respuesta, reverse("panel_trabajos"))
        trabajo.refresh_from_db()
        self.assertEqual(trabajo.titulo, "Título nuevo")
        self.assertEqual(trabajo.fotos.count(), 2)

    def test_agrega_las_fotos_nuevas_despues_de_las_existentes(self):
        trabajo = crear_trabajo(fotos=2)

        self.client.post(
            self.url(trabajo),
            datos_de_formulario(fotos=[imagen_de_prueba("nueva.jpg")]),
        )

        fotos = list(trabajo.fotos.all())
        self.assertEqual(len(fotos), 3)
        self.assertIn("nueva", fotos[-1].imagen.name)

    def test_conserva_la_portada_al_agregar_fotos(self):
        trabajo = crear_trabajo(fotos=2)
        portada = trabajo.portada

        self.client.post(
            self.url(trabajo),
            datos_de_formulario(fotos=[imagen_de_prueba("nueva.jpg")]),
        )

        self.assertEqual(Trabajo.objects.get(id=trabajo.id).portada, portada)

    def test_muestra_las_fotos_actuales(self):
        trabajo = crear_trabajo(fotos=2)

        respuesta = self.client.get(self.url(trabajo))

        for foto in trabajo.fotos.all():
            self.assertContains(respuesta, foto.imagen.url)

    def test_responde_404_si_no_existe(self):
        self.assertEqual(
            self.client.get(reverse("editar_trabajo", args=[999])).status_code,
            404,
        )


class EliminarFotoTests(PruebaDePanel):
    def test_elimina_la_foto_y_vuelve_a_la_edicion(self):
        trabajo = crear_trabajo(fotos=2)
        foto = trabajo.fotos.first()

        respuesta = self.client.post(
            reverse("eliminar_foto_trabajo", args=[foto.id])
        )

        self.assertRedirects(
            respuesta, reverse("editar_trabajo", args=[trabajo.id])
        )
        self.assertEqual(trabajo.fotos.count(), 1)

    def test_no_elimina_la_ultima_foto(self):
        trabajo = crear_trabajo(fotos=1)
        foto = trabajo.fotos.get()

        self.client.post(reverse("eliminar_foto_trabajo", args=[foto.id]))

        self.assertEqual(trabajo.fotos.count(), 1)

    def test_solo_acepta_post(self):
        trabajo = crear_trabajo(fotos=2)
        foto = trabajo.fotos.first()

        respuesta = self.client.get(
            reverse("eliminar_foto_trabajo", args=[foto.id])
        )

        self.assertEqual(respuesta.status_code, 405)
        self.assertEqual(trabajo.fotos.count(), 2)


class ElegirPortadaTests(PruebaDePanel):
    def test_la_foto_elegida_pasa_a_ser_la_portada(self):
        trabajo = crear_trabajo(fotos=3)
        primera, segunda, tercera = trabajo.fotos.all()

        respuesta = self.client.post(
            reverse("portada_foto_trabajo", args=[tercera.id])
        )

        self.assertRedirects(
            respuesta, reverse("editar_trabajo", args=[trabajo.id])
        )
        self.assertEqual(list(trabajo.fotos.all()), [tercera, primera, segunda])

    def test_solo_acepta_post(self):
        trabajo = crear_trabajo(fotos=2)
        primera, segunda = trabajo.fotos.all()

        respuesta = self.client.get(
            reverse("portada_foto_trabajo", args=[segunda.id])
        )

        self.assertEqual(respuesta.status_code, 405)
        self.assertEqual(list(trabajo.fotos.all()), [primera, segunda])


class EliminarTrabajoTests(PruebaDePanel):
    def test_pide_confirmacion_antes_de_eliminar(self):
        trabajo = crear_trabajo()

        respuesta = self.client.get(
            reverse("eliminar_trabajo", args=[trabajo.id])
        )

        self.assertContains(respuesta, trabajo.titulo)
        self.assertTrue(Trabajo.objects.filter(id=trabajo.id).exists())

    def test_elimina_el_trabajo_al_confirmar(self):
        trabajo = crear_trabajo()

        respuesta = self.client.post(
            reverse("eliminar_trabajo", args=[trabajo.id])
        )

        self.assertRedirects(respuesta, reverse("panel_trabajos"))
        self.assertFalse(Trabajo.objects.filter(id=trabajo.id).exists())
