from django.shortcuts import get_object_or_404, redirect, render

from alumcris.access import administrador_requerido
from trabajos.models import Trabajo

from .forms import ProductosForm
from .models import Producto

MAXIMO_DESTACADOS = 5


def inicio(request):
    productos = Producto.objects.filter(publicado=True)[:3]
    destacados = (
        Trabajo.objects.visibles()
        .filter(destacado=True)
        .prefetch_related("fotos")[:MAXIMO_DESTACADOS]
    )

    return render(
        request,
        "paginas/inicio.html",
        {
            "productos": productos,
            "destacados": destacados,
        },
    )


def catalogo(request):
    productos = Producto.objects.filter(publicado=True)

    return render(
        request,
        "paginas/productos.html",
        {"productos": productos},
    )


def detalle_producto(request, id):
    producto = get_object_or_404(Producto, id=id, publicado=True)

    return render(
        request,
        "paginas/detalle_producto.html",
        {"producto": producto},
    )


@administrador_requerido
def panel(request):
    productos = Producto.objects.all()

    return render(
        request,
        "administracion/index.html",
        {"productos": productos},
    )


@administrador_requerido
def crear_producto(request):
    formulario = ProductosForm(
        request.POST or None,
        request.FILES or None,
    )

    if formulario.is_valid() and request.POST:
        formulario.save()
        return redirect("panel")

    return render(
        request,
        "administracion/crear.html",
        {"formulario": formulario},
    )


@administrador_requerido
def editar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)

    formulario = ProductosForm(
        request.POST or None,
        request.FILES or None,
        instance=producto,
    )

    if formulario.is_valid() and request.POST:
        formulario.save()
        return redirect("panel")

    return render(
        request,
        "administracion/editar.html",
        {
            "formulario": formulario,
            "producto": producto,
        },
    )


@administrador_requerido
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)

    if request.method == "POST":
        producto.delete()
        return redirect("panel")

    return render(
        request,
        "administracion/eliminar.html",
        {"producto": producto},
    )