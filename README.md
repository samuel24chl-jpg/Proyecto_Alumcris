# Alumcris

Sitio web para **Alumcris**, empresa dedicada a la fabricación e instalación de ventanas de aluminio y PVC, puertas y soluciones de vidrio (mamparas, termopaneles, shower doors) para proyectos residenciales y comerciales.

El sitio permite que los clientes conozcan el catálogo de productos, vean trabajos realizados y soliciten cotizaciones en línea. Un panel administrativo permite al equipo de la empresa gestionar el contenido y dar seguimiento a las solicitudes.

## Funcionalidades

### Sitio público

- **Inicio**: presentación de la empresa, servicios y productos destacados.
- **Catálogo de productos**: ventanas correderas, proyectantes, fijas, abatibles, puertas, termopaneles y más, en aluminio, PVC o vidrio, con su página de detalle.
- **Galería de trabajos**: proyectos terminados con fotos, comuna y fecha, filtrables por material y tipo.
- **Solicitud de cotización**: el cliente elige un producto e indica sus medidas (ancho y alto en cm) y la cantidad. El sistema calcula automáticamente la superficie total en m².

### Panel administrativo (requiere iniciar sesión como personal)

- **Productos**: crear, editar, eliminar y publicar u ocultar productos.
- **Trabajos**: gestionar los proyectos de la galería, subir varias fotos, elegir la portada y marcar trabajos destacados. Las fotos se optimizan al subirse y se les eliminan los metadatos, incluida la ubicación GPS.
- **Cotizaciones**: revisar las solicitudes y cambiar su estado (*Pendiente*, *En revisión*, *Aprobada* o *Rechazada*).

## Tecnologías

| Componente | Herramienta |
|---|---|
| Lenguaje | Python 3.13 |
| Framework web | Django 6.1 |
| Base de datos | MariaDB / MySQL (`mysqlclient`) |
| Interfaz | Plantillas de Django + Bootstrap 5.3 |
| Imágenes | Pillow |
| Configuración | python-dotenv (variables de entorno en `.env`) |
| Pruebas | `unittest` de Django + coverage.py |


## Licencia

Este proyecto se distribuye bajo la licencia **GNU GPL v3**. Ver el archivo [LICENSE](LICENSE).
