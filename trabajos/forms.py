from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max

from alumcris.formularios import EstilosBootstrapMixin
from productos.opciones import MATERIALES, TIPOS

from .models import FotoTrabajo, Trabajo


class EntradaVariasImagenes(forms.FileInput):
    allow_multiple_selected = True


class CampoVariasImagenes(forms.ImageField):
    """Valida una por una las imágenes subidas en un mismo campo."""

    widget = EntradaVariasImagenes
    default_error_messages = {
        "required": "Debes subir al menos una foto.",
    }

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise ValidationError(
                    self.error_messages["required"],
                    code="required",
                )
            return []

        validar_imagen = super().clean
        return [validar_imagen(archivo, initial) for archivo in data]


class TrabajoForm(EstilosBootstrapMixin, forms.ModelForm):
    fotos = CampoVariasImagenes(label="Fotos")

    class Meta:
        model = Trabajo
        fields = [
            "titulo",
            "material",
            "tipo",
            "comuna",
            "fecha",
            "descripcion",
            "producto",
            "destacado",
            "publicado",
        ]
        widgets = {
            "fecha": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
        }
        help_texts = {
            "producto": "Opcional. Se preselecciona cuando el cliente pide una cotización desde este trabajo.",
            "destacado": "Aparece en el carrusel del inicio, que muestra los 5 más recientes.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields["fotos"].required = False
            self.fields["fotos"].label = "Agregar más fotos"
            self.fields["fotos"].help_text = "Se suman a las fotos actuales."
        else:
            self.fields["fotos"].help_text = (
                "Puedes seleccionar varias. La primera será la portada."
            )

        self.fields["material"].choices = [("", "Selecciona un material"), *MATERIALES]
        self.fields["tipo"].choices = [("", "Selecciona un tipo"), *TIPOS]
        self.fields["producto"].empty_label = "Sin producto relacionado"

    @transaction.atomic
    def save(self):
        trabajo = super().save()

        ultimo_orden = trabajo.fotos.aggregate(Max("orden"))["orden__max"]
        siguiente_orden = 0 if ultimo_orden is None else ultimo_orden + 1

        for orden, archivo in enumerate(
            self.cleaned_data["fotos"],
            start=siguiente_orden,
        ):
            FotoTrabajo.objects.create(
                trabajo=trabajo,
                imagen=archivo,
                orden=orden,
            )

        return trabajo
