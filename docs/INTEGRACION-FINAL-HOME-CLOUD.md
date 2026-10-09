# Integración final HOME y Cloud

Este informe actualiza los pendientes del informe anterior. La arquitectura sigue siendo Flask; los textos corporativos y enlaces aprobados del Hero se conservan. No se modificaron rutas, formularios, autenticación, administración, configuración de Render ni datos de producción.

| Recurso | Original | Dimensiones originales | Bytes originales | Destino | Dimensiones WebP | Bytes WebP |
|---|---|---|---:|---|---|---:|
| hero-afcyber | C:\PROYECTOS DE PROGRAMAS\PARA-WED-PUBLICACION\Imagenes wed\Centro de ciberseguridad futurista nocturno.png | 1672×941 | 2029455 | C:\PROYECTOS DE PROGRAMAS\PARA-WED-PUBLICACION\static\images\corporativas\hero-afcyber.webp | 1672×941 | 191330 |
| servicio-cloud | C:\PROYECTOS DE PROGRAMAS\PARA-WED-PUBLICACION\Imagenes wed\Infraestructura global en la nube.png | 1672×941 | 2130248 | C:\PROYECTOS DE PROGRAMAS\PARA-WED-PUBLICACION\static\images\corporativas\servicio-cloud.webp | 1200×675 | 153672 |

Ambos originales se comprobaron visualmente y son ilustraciones conceptuales, no fotografías de instalaciones reales. No se aumentó artificialmente el Hero a 1920 px: conserva 1672×941. Cada imagen tiene variantes de 640 y 960 px, srcset/sizes y dimensiones explícitas. HOME carga con prioridad alta, sin lazy loading; Cloud usa lazy loading y decoding async. El Hero usa una imagen HTML con object-fit cover y encuadre responsive; la superposición oscura permite conservar contenido a la izquierda y monitores a la derecha. El encuadre del fondo varía con la pantalla para priorizar su legibilidad.

## Cloud y catálogo
No existe servicio Cloud declarado en los ocho servicios iniciales del proyecto ni en el catálogo de prueba. No se consultó la base real. La imagen queda integrada en el componente reutilizable para cualquier servicio existente cuyo nombre incluya cloud o nube; no se creó servicio, página o sección comercial. La presentación de esa tarjeta se probó aislada usando un objeto de prueba, sin insertarlo en base de datos.

## Archivos modificados en esta fase
- templates/public/index.html: ilustración de portada y conservación de textos y enlaces actuales.
- templates/public/partials/corporate-images.html: asignación de Cloud.
- static/css/corporate-images.css: fondo, overlay y responsive de Hero.
- scripts/optimize_corporate_images.py: dos asignaciones nuevas.
- tests/test_corporate_images.py: prioridad del nuevo Hero y selección de Cloud.
- docs/IMAGENES-CORPORATIVAS.json: dimensiones, hashes y variantes actualizados.
- static/images/corporativas/: seis archivos WebP nuevos, sin eliminar ni alterar los 36 anteriores.
- Este informe y nota de actualización en el informe anterior.

## Verificación
- 30 pruebas automatizadas aprobadas con base y almacenamiento aislados.
- 66 combinaciones de 11 rutas y seis anchos: 1920, 1366, 1024, 768, 390 y 375 px; sin scroll horizontal ni errores JavaScript.
- Cloud comprobado en seis anchos con proporción 16:9; ambos recursos principales HTTP 200 e image/webp.
- Capturas de Hero 1366 y 375 revisadas visualmente; texto y botones legibles.
- 36 WebP anteriores conservan sus hashes exactamente; originales nuevos y anteriores permanecen intactos.
- Git no ignora las imágenes nuevas. git diff --check correcto; cambios sin commit.
- Se conservaron cambios previos y eliminaciones ajenas existentes.

## Pendientes
Confirmar con el propietario si Cloud debe declararse como servicio comercial en el catálogo real. Mientras tanto no se añade contenido nuevo. La preparación local de assets y rutas estáticas no sustituye una comprobación posterior en Render una vez autorizado el despliegue.

No se hizo push, deploy ni modificación de producción.
