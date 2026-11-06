from django.shortcuts import get_object_or_404, redirect, render

from alumcris.access import administrador_requerido

from .forms import CotizacionForm, EstadoCotizacionForm
from .models import Cotizacion


def crear_cotizacion(request):
    producto_id = request.GET.get("producto")

    formulario = CotizacionForm(
        request.POST or None,
        initial={"producto": producto_id},
    )

    if formulario.is_valid() and request.POST:
        cotizacion = formulario.save(commit=False)

        cotizacion.superficie_total = round(
            (
                cotizacion.ancho
                * cotizacion.alto
                * cotizacion.cantidad
            ) / 10000,
            2,
        )

        cotizacion.save()
        return redirect("cotizacion_exito")

    return render(
        request,
        "cotizaciones/crear.html",
        {"formulario": formulario},
    )


def cotizacion_exito(request):
    return render(
        request,
        "cotizaciones/exito.html",
    )


@administrador_requerido
def panel_cotizaciones(request):
    cotizaciones = Cotizacion.objects.all().order_by(
        "-fecha_solicitud"
    )

    return render(
        request,
        "cotizaciones/index.html",
        {"cotizaciones": cotizaciones},
    )


@administrador_requerido
def editar_cotizacion(request, id):
    cotizacion = get_object_or_404(Cotizacion, id=id)

    formulario = CotizacionForm(
        request.POST or None,
        instance=cotizacion,
    )

    if formulario.is_valid() and request.POST:
        cotizacion = formulario.save(commit=False)

        cotizacion.superficie_total = round(
            (
                cotizacion.ancho
                * cotizacion.alto
                * cotizacion.cantidad
            ) / 10000,
            2,
        )

        cotizacion.save()
        return redirect("panel_cotizaciones")

    return render(
        request,
        "cotizaciones/editar.html",
        {
            "formulario": formulario,
            "cotizacion": cotizacion,
        },
    )


@administrador_requerido
def cambiar_estado(request, id):
    cotizacion = get_object_or_404(Cotizacion, id=id)

    formulario = EstadoCotizacionForm(
        request.POST or None,
        instance=cotizacion,
    )

    if formulario.is_valid() and request.POST:
        formulario.save()
        return redirect("panel_cotizaciones")

    return render(
        request,
        "cotizaciones/estado.html",
        {
            "formulario": formulario,
            "cotizacion": cotizacion,
        },
    )


@administrador_requerido
def eliminar_cotizacion(request, id):
    cotizacion = get_object_or_404(Cotizacion, id=id)

    if request.method == "POST":
        cotizacion.delete()
        return redirect("panel_cotizaciones")

    return render(
        request,
        "cotizaciones/eliminar.html",
        {"cotizacion": cotizacion},
    )