from django.urls import path
from . import views

urlpatterns = [
    path('crear/', views.crear_cotizacion, name='crear_cotizacion'),
    path('exito/', views.cotizacion_exito, name='cotizacion_exito'),
    path('panel/', views.panel_cotizaciones, name='panel_cotizaciones'),
    path('editar/<int:id>/', views.editar_cotizacion, name='editar_cotizacion'),
    path('estado/<int:id>/', views.cambiar_estado, name='cambiar_estado'),
    path('eliminar/<int:id>/', views.eliminar_cotizacion, name='eliminar_cotizacion'),
]