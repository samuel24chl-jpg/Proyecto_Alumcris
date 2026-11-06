from django.contrib import admin

from .models import FotoTrabajo, Trabajo


class FotoTrabajoInline(admin.TabularInline):
    model = FotoTrabajo
    extra = 1


@admin.register(Trabajo)
class TrabajoAdmin(admin.ModelAdmin):
    list_display = ["titulo", "tipo", "material", "comuna", "fecha", "destacado", "publicado"]
    inlines = [FotoTrabajoInline]
