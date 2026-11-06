from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

LADO_MAXIMO = 1920
CALIDAD_WEBP = 82


def optimizar_imagen(archivo):
    """Reduce la foto y descarta sus metadatos, incluida la ubicación GPS."""
    archivo.seek(0)

    with Image.open(archivo) as original:
        imagen = ImageOps.exif_transpose(original).convert("RGB")

    imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO), Image.Resampling.LANCZOS)

    salida = BytesIO()
    imagen.save(salida, "WEBP", quality=CALIDAD_WEBP)

    return ContentFile(
        salida.getvalue(),
        name=f"{Path(archivo.name).stem}.webp",
    )
