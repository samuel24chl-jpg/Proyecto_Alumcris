from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import never_cache


def administrador_requerido(view):
    """Permite el acceso únicamente a administradores activos."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                "ingresar",
            )

        if not (request.user.is_active and request.user.is_staff):
            raise PermissionDenied

        return view(request, *args, **kwargs)

    return never_cache(wrapped)