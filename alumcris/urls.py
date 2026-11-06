from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.templatetags.static import static
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path(
        "favicon.ico",
        RedirectView.as_view(url=static("favicon.png")),
    ),
    path(
        "ingresar/",
        LoginView.as_view(
            template_name="administracion/ingresar.html",
            authentication_form=AdminAuthenticationForm,
        ),
        name="ingresar",
    ),
    path(
        "salir/",
        LogoutView.as_view(),
        name="salir",
    ),
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "cotizaciones/",
        include("cotizaciones.urls"),
    ),
    path(
        "",
        include("trabajos.urls"),
    ),
    path(
        "",
        include("productos.urls"),
    ),
]