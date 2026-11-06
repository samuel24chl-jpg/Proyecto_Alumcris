from django.urls import path

from . import views

urlpatterns = [
    path('trabajos/', views.galeria, name='galeria'),
    path('trabajos/<int:id>/', views.detalle_trabajo, name='detalle_trabajo'),
    path('panel/trabajos/', views.panel_trabajos, name='panel_trabajos'),
    path('panel/trabajos/crear/', views.crear_trabajo, name='crear_trabajo'),
    path('panel/trabajos/editar/<int:id>/', views.editar_trabajo, name='editar_trabajo'),
    path('panel/trabajos/eliminar/<int:id>/', views.eliminar_trabajo, name='eliminar_trabajo'),
    path('panel/trabajos/fotos/<int:id>/eliminar/', views.eliminar_foto_trabajo, name='eliminar_foto_trabajo'),
    path('panel/trabajos/fotos/<int:id>/portada/', views.portada_foto_trabajo, name='portada_foto_trabajo'),
]
