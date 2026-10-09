# Integración de imágenes corporativas — AFCyber Solutions

## Estado final

Los 14 recursos previstos están identificados y optimizados: 10 se muestran en las páginas locales y 4 están justificadamente reservados. HOME utiliza la nueva ilustración aprobada, conservando los textos y botones anteriores. Cloud tiene su imagen y asignación en el componente del catálogo, pero no se creó un servicio comercial inexistente.

Arquitectura canónica: GET / → templates/public/index.html → templates/public/base.html. No se utilizan los HTML raíz del despliegue estático anterior.

## Auditoría

Se examinaron 16 originales (14 JPEG y 2 PNG). No hay archivos dañados ni duplicados exactos por hash de archivo. Los dos PNG fueron identificados visualmente, no solo por nombre: monitores y servidores con zona oscura izquierda para HOME; nube luminosa, servidores y dispositivos conectados para Cloud. Sus nombres reales son distintos de los nombres solicitados para los derivados.

Todos los originales seleccionados conservan sus hashes. Las 36 variantes WebP anteriores permanecen idénticas. Se conservaron los cambios previos y las eliminaciones ajenas existentes en Git.

## Recursos y asignaciones

Los originales se encuentran en `C:/PROYECTOS DE PROGRAMAS/PARA-WED-PUBLICACION/Imagenes wed/`. Todos los derivados se encuentran en `static/images/corporativas/`.

| Recurso WebP | Original | Dimensiones originales | Original KiB | WebP principal | WebP KiB | Estado/ubicación |
|---|---|---|---:|---|---:|---|
| hero-afcyber.webp | Centro de ciberseguridad futurista nocturno.png | 1672×941 | 1981.9 | 1672×941 | 186.8 | Integrada en HOME, carga prioritaria |
| servicio-cloud.webp | Infraestructura global en la nube.png | 1672×941 | 2080.3 | 1200×675 | 150.1 | Asignación lista para Cloud; reservado porque el catálogo local no declara ese servicio |
| ceo-amauri-tecnologia.webp | WhatsApp Image 2026-10-08 at 20.41.33 (1).jpeg | 1122×1402 | 149.2 | 1000×1250 | 80.0 | Reservada: alternativa del fundador; evita duplicar el perfil |
| ceo-amauri-institucional.webp | WhatsApp Image 2026-10-08 at 20.41.33.jpeg | 1122×1402 | 114.6 | 1000×1250 | 58.2 | Integrada en HOME y Nosotros |
| servicio-ciberseguridad.webp | WhatsApp Image 2026-10-08 at 20.41.33 (2).jpeg | 1600×900 | 277.9 | 1200×675 | 141.5 | Integrada en HOME y catálogo |
| servicio-software.webp | WhatsApp Image 2026-10-08 at 20.41.33 (3).jpeg | 1600×900 | 251.7 | 1200×675 | 132.3 | Integrada en HOME y catálogo |
| servicio-redes.webp | WhatsApp Image 2026-10-08 at 20.41.33 (4).jpeg | 1600×900 | 325.4 | 1200×675 | 170.3 | Reservada para categoría de redes existente; no se crea un servicio |
| servicio-soporte.webp | WhatsApp Image 2026-10-08 at 20.41.34 (1).jpeg | 1600×900 | 253.8 | 1200×675 | 134.7 | Integrada en HOME y catálogo |
| servicio-control-acceso.webp | WhatsApp Image 2026-10-08 at 20.41.34 (2).jpeg | 1600×900 | 146.6 | 1200×675 | 63.5 | Reservada para categoría independiente; la combinada actual utiliza CCTV |
| nosotros-valores.webp | WhatsApp Image 2026-10-08 at 20.41.34 (3).jpeg | 1600×900 | 208.4 | 1600×900 | 143.7 | Integrada en Nosotros; evita duplicarla en HOME |
| politica-calidad.webp | WhatsApp Image 2026-10-08 at 20.41.34 (4).jpeg | 1600×900 | 221.0 | 1200×675 | 107.4 | Integrada en Política de Calidad |
| contacto-afcyber.webp | WhatsApp Image 2026-10-08 at 20.41.34 (5).jpeg | 1600×901 | 185.7 | 1200×676 | 91.0 | Integrada en Contacto |
| servicio-cctv.webp | WhatsApp Image 2026-10-08 at 20.41.34.jpeg | 1600×900 | 270.6 | 1200×675 | 139.0 | Integrada en HOME y catálogo |
| productos-software-afcyber.webp | WhatsApp Image 2026-10-08 at 20.41.35.jpeg | 1600×900 | 211.3 | 1600×900 | 137.5 | Integrada en planes/soluciones del catálogo existente |

Los dos originales alternativos de atención (`20.41.34 (6).jpeg`) y productos (`20.41.35 (1).jpeg`) permanecen intactos sin publicar. No representan recursos pendientes adicionales.

## Optimización y presentación

- 42 archivos WebP, tres variantes por cada uno de los 14 recursos.
- Escenas: 640, 960 y resolución máxima asignada; retratos: 320, 640 y 1000 px.
- WebP calidad 84, método 6; compresión con pérdida visualmente revisada, no una conversión matemáticamente sin pérdida.
- No se aumentó artificialmente la resolución: HOME conserva 1672×941; Cloud queda en 1200×675.
- Los recursos usan url_for, srcset, sizes, dimensiones explícitas, alt y decoding async. HOME tiene fetchpriority high sin lazy loading; secundarios usan lazy loading.
- Hero: overlay oscuro, texto HTML a la izquierda y elementos tecnológicos a la derecha; encuadre adaptado en móvil, sin deformar.
- Retratos completos con object-fit contain; proporción 4:5.
- Las escenas generadas se presentan como ilustraciones conceptuales, sin afirmar que muestran oficinas, empleados o proyectos reales.
- Productos permanece dentro del catálogo actual; no se añadió página o sección independiente.

## Archivos de la integración

Plantillas modificadas: `templates/public/base.html`, `index.html`, `catalog.html`, `contact.html`, `quality.html`, `partials/identity.html` y `partials/founder-profile.html`. Componente nuevo: `templates/public/partials/corporate-images.html`.

CSS nuevo: `static/css/corporate-images.css`. Optimización: `scripts/optimize_corporate_images.py`. Pruebas: `tests/test_corporate_images.py`. Inventario completo con rutas, bytes, dimensiones y hashes: `docs/IMAGENES-CORPORATIVAS.json`.

Cambio mínimo de compatibilidad anterior en `app.py`: registro MIME image/webp. No se modifican seguridad, formularios, rutas administrativas ni modelos.

En esta última comprobación solo se actualiza este informe: las dos imágenes correctas ya estaban convertidas e integradas; se evita sobrescribirlas innecesariamente.

## Pruebas y limitaciones

- Suite completa repetida: 30 pruebas automatizadas aprobadas, con SQLite en memoria y almacenamiento aislado.
- Responsive: 66 combinaciones de 11 rutas en 1920, 1366, 1024, 768, 390 y 375 px; sin scroll horizontal ni errores JavaScript.
- Cloud comprobado como tarjeta aislada en seis anchos; no se insertó un servicio de prueba en producción.
- Ambos recursos principales responden HTTP 200 con image/webp. Variantes y demás imágenes comprobadas mediante suite y decodificación en navegador.
- Capturas HOME de escritorio y móvil revisadas; botones y texto legibles. Menú móvil, navegación por teclado y etiquetas comprobados.
- Formularios, CSRF, autenticación, descargas privadas, legales y administración siguen cubiertos por pruebas.
- Git no ignora las imágenes nuevas. git diff --check correcto; trabajo sin commit.
- Aviso existente de SQLAlchemy sobre Query.get legacy: no provoca fallos; no se cambió backend por esta integración.

Cloud no aparece en los ocho servicios iniciales ni en el catálogo local. No se consultó la base real. Para mostrarlo comercialmente deberá existir una categoría aprobada; el componente ya asigna su ilustración a nombres con cloud o nube. Las imágenes de redes y control independiente siguen el mismo criterio, sin inventar servicios.

Resultados y capturas locales: `.verification/home-cloud-responsive.json`, `.verification/hero-final-1366.png` y `.verification/hero-final-375.png`. Estos archivos de verificación están excluidos de Git.

No se hizo push, deploy ni modificación de datos de producción. El trabajo queda preparado para revisión y autorización.
