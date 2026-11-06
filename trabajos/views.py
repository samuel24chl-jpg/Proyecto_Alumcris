from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from alumcris.access import administrador_requerido
from productos.opciones import MATERIALES, TIPOS

from .forms import TrabajoForm
from .models import FotoTrabajo, Trabajo

TRABAJOS_POR_PAGINA = 9


def _filtro_valido(request, nombre, opciones):
    """Devuelve el filtro solicitado solo si es una opción existente."""
    valor = request.GET.get(nombre, "")
    return valor if valor in dict(opciones) else ""


def galeria(request):
    material = _filtro_valido(request, "material", MATERIALES)
    tipo = _filtro_valido(request, "tipo", TIPOS)
    filtros = {
        campo: valor
        for campo, valor in (("material", material), ("tipo", tipo))
        if valor
    }

    trabajos = (
        Trabajo.objects.visibles()
        .filter(**filtros)
        .prefetch_related("fotos")
    )
    pagina = Paginator(trabajos, TRABAJOS_POR_PAGINA).get_page(
        request.GET.get("pagina")
    )

    return render(
        request,
        "trabajos/galeria.html",
        {
            "pagina": pagina,
            "materiales": MATERIALES,
            "tipos": TIPOS,
            "material": material,
            "tipo": tipo,
            "filtros": urlencode(filtros),
        },
    )


def detalle_trabajo(request, id):
    trabajo = get_object_or_404(
        Trabajo.objects.visibles().prefetch_related("fotos"),
        id=id,
    )

    return render(
        request,
        "trabajos/detalle.html",
        {"trabajo": trabajo},
    )


@administrador_requerido
def panel_trabajos(request):
    trabajos = Trabajo.objects.prefetch_related("fotos")

    return render(
        request,
        "trabajos/index.html",
        {"trabajos": trabajos},
    )


@administrador_requerido
def crear_trabajo(request):
    formulario = TrabajoForm(
        request.POST or None,
        request.FILES or None,
    )

    if formulario.is_valid():
        formulario.save()
        return redirect("panel_trabajos")

    return render(
        request,
        "trabajos/crear.html",
        {"formulario": formulario},
    )


@administrador_requerido
def editar_trabajo(request, id):
    trabajo = get_object_or_404(Trabajo, id=id)

    formulario = TrabajoForm(
        request.POST or None,
        request.FILES or None,
        instance=trabajo,
    )

    if formulario.is_valid():
        formulario.save()
        return redirect("panel_trabajos")

    return render(
        request,
        "trabajos/editar.html",
        {
            "formulario": formulario,
            "trabajo": trabajo,
            "fotos": trabajo.fotos.all(),
        },
    )


@administrador_requerido
def eliminar_trabajo(request, id):
    trabajo = get_object_or_404(Trabajo, id=id)

    if request.method == "POST":
        trabajo.delete()
        return redirect("panel_trabajos")

    return render(
        request,
        "trabajos/eliminar.html",
        {"trabajo": trabajo},
    )


@administrador_requerido
@require_POST
def eliminar_foto_trabajo(request, id):
    foto = get_object_or_404(FotoTrabajo, id=id)
    trabajo = foto.trabajo

    # Un trabajo siempre conserva al menos una foto para poder mostrarse.
    if trabajo.fotos.count() > 1:
        foto.delete()

    return redirect("editar_trabajo", trabajo.id)


@administrador_requerido
@require_POST
def portada_foto_trabajo(request, id):
    elegida = get_object_or_404(FotoTrabajo, id=id)
    trabajo = elegida.trabajo

    fotos = [elegida, *trabajo.fotos.exclude(id=elegida.id)]

    for orden, foto in enumerate(fotos):
        foto.orden = orden

    FotoTrabajo.objects.bulk_update(fotos, ["orden"])

    return redirect("editar_trabajo", trabajo.id)
