from django import forms


class EstilosBootstrapMixin:
    """Agrega a cada campo la clase de Bootstrap que corresponde a su tipo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for campo in self.fields.values():
            campo.widget.attrs["class"] = self._clase_bootstrap(campo.widget)

    @staticmethod
    def _clase_bootstrap(widget):
        if isinstance(widget, forms.CheckboxInput):
            return "form-check-input"

        if isinstance(widget, forms.Select):
            return "form-select"

        return "form-control"
