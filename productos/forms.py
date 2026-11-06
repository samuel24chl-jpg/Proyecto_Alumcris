from django import forms

from alumcris.formularios import EstilosBootstrapMixin

from .models import Producto
from .opciones import MATERIALES, TIPOS

class ProductosForm(EstilosBootstrapMixin, forms.ModelForm):
    nombre = forms.CharField(
        min_length=3,
        max_length=100,
        label='Nombre del producto',
        widget=forms.TextInput(attrs={'oninput': "this.value = this.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ ]/g, '')"})
    )

    descripcion = forms.CharField(
        min_length=10,
        widget=forms.Textarea,
        label='Descripción'
    )
    material = forms.ChoiceField(choices=MATERIALES, label='Material')

    tipo = forms.ChoiceField(choices=TIPOS, label='Tipo de producto')

    class Meta:
        model = Producto
        fields = [
            'nombre',
            'material',
            'tipo',
            'descripcion',
            'imagen',
            'publicado'
        ]