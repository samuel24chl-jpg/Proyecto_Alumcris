from django import forms

from alumcris.formularios import EstilosBootstrapMixin

from .models import Cotizacion
from productos.models import Producto

class CotizacionForm(EstilosBootstrapMixin, forms.ModelForm):

    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(publicado=True),
        label='Producto solicitado',
        empty_label='Selecciona un producto'
    )

    nombre_cliente = forms.CharField(
        min_length=3,
        max_length=100,
        label='Nombre del cliente',
        widget=forms.TextInput(attrs={'oninput': "this.value = this.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ ]/g, '')"})
    )


    telefono = forms.CharField(
        min_length=9,
        max_length=9,
        label='Teléfono',
        widget=forms.TextInput(attrs={'oninput': "this.value = this.value.replace(/[^0-9]/g, '')",'inputmode': 'numeric'})
    )


    ancho = forms.DecimalField(
        max_digits=7,
        decimal_places=2,
        min_value=1,
        label='Ancho (cm)'
    )

    alto = forms.DecimalField(
        max_digits=7,
        decimal_places=2,
        min_value=1,
        label='Alto (cm)'
    )

    cantidad = forms.IntegerField(
        min_value=1,
        label='Cantidad'
    )
    
    class Meta:
        model = Cotizacion
        fields = [
            'producto',
            'nombre_cliente',
            'telefono',
            'ancho',
            'alto',
            'cantidad'
        ]

class EstadoCotizacionForm(EstilosBootstrapMixin, forms.ModelForm):

    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En revision', 'En revisión'),
        ('Aprobada', 'Aprobada'),
        ('Rechazada', 'Rechazada'),
    ]

    estado = forms.ChoiceField(
        choices=ESTADOS,
        label='Estado de la cotización'
    )

    class Meta:
        model = Cotizacion
        fields = ['estado']
