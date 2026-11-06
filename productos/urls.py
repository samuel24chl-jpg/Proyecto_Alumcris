from django.urls import path
from . import views
from django.contrib.staticfiles.urls import static
from django.conf import settings

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('productos/', views.catalogo, name='catalogo'),
    path('productos/<int:id>/', views.detalle_producto, name='detalle_producto'),
    path('panel/', views.panel, name='panel'),
    path('panel/crear/', views.crear_producto, name='crear_producto'),
    path('panel/editar/<int:id>/', views.editar_producto, name='editar_producto'),
    path('panel/eliminar/<int:id>/', views.eliminar_producto, name='eliminar_producto'),       
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)