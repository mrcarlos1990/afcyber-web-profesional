# AFCyber Solutions — revisión final del 8 de octubre de 2026

## Estado y alcance

Se continuó desde el trabajo existente, sin reconstruir el proyecto ni revertir cambios. Git está en `main`, sin merge/rebase pendiente y con dos commits locales por delante de `origin/main`. No se hizo commit, push ni deploy en esta continuación. No se conectó a la base de producción.

Al comenzar había ocho archivos rastreados modificados, cuatro archivos de frontend/pruebas sin rastrear y dos informes anteriores en `docs/`. El conteo recibido de 14 archivos y +224/-7 líneas no se reproduce literalmente en el diff de los archivos rastreados. Se revisó el contenido efectivo, incluyendo archivos sin rastrear, sin asumir que faltaban cambios.

También había diez imágenes originales de raíz eliminadas por trabajo ajeno. Esas eliminaciones no se restauraron ni se incluyeron en cambios de esta tarea. No se borraron imágenes, información, rutas ni funcionalidades.

## Arquitectura canónica

`GET /` → `app.py:index()` → `templates/public/index.html` → `templates/public/base.html`.

CSS: `platform.css`, `home.css`, `corporate.css`. JavaScript: Bootstrap y `platform.js`. Los wrappers de navegación/footer incluyen los componentes corporativos. Identidad y contactos se leen de `static/data/company.json`.

Los HTML de raíz, `netlify.toml`, `static/js/main.js` y `scripts/build_corporate.py` pertenecen al despliegue estático legacy. Se conservan para no romper sus dependencias; no se usaron ni regeneraron para Render.

La captura pública recuperada el 6 de octubre mostraba el HOME anterior y las nuevas rutas corporativas/legales respondían 404. No se volvió a auditar el servicio público en esta continuación. Los commits locales no publicados explican la diferencia observada; no se pudo verificar el commit activo ni la configuración del panel de Render.

## Archivos del trabajo acumulado revisado

Nueve archivos rastreados modificados:

1. `app.py`: FAQ pública y sitemap; corrige URL base de Descargas conservando sus tres rutas.
2. `templates/public/index.html`: HOME compacto, branding, contacto, FAQ limitada, componentes compartidos.
3. `templates/public/partials/identity.html`: enlace directo a Política de Calidad.
4. `static/css/home.css`: proporciones responsive, fundador, pilares y contraste del enlace activo.
5. `static/js/platform.js`: cierre del menú incluso si se pulsa el CTA durante la apertura.
6. `render.yaml`: arranque con migraciones antes de Gunicorn.
7. `Procfile`: mismo comando de arranque.
8. `README.md`: arquitectura canónica, legacy y requisitos de publicación.
9. `scripts/build_corporate.py`: identifica su función exclusivamente legacy.

Cinco archivos sin rastrear que deben incluirse al preparar el commit del trabajo:

10. `templates/public/faq.html`.
11. `templates/public/partials/faq.html`.
12. `tests/test_corporate.py`: conservado, revisado y actualizado para contactos compactos en HOME.
13. `tests/test_public_architecture.py`.
14. `docs/REVISION-FINAL-2026-10-08.md`.

Los informes anteriores `ACTUALIZACION-CORPORATIVA.md` y `LEGAL-PRESTAMOS-PROPUESTA.md` se conservaron. El estado pendiente de rebase descrito en el primero es histórico; este informe recoge el estado actual. Scripts, bases, paquetes de verificación y capturas quedan bajo `.verification/`, excluido de Git.

## Problemas y correcciones

- No había que modificar el HTML raíz para Render: se mantuvo Flask como implementación canónica.
- Las pestañas de Descargas generaban rutas anidadas inexistentes. Se corrigió la URL base sin cambiar endpoints, permisos ni almacenamiento.
- HOME repetía contactos departamentales y acumulaba preguntas: ahora enlaza al directorio de contacto, muestra como máximo tres FAQ y mantiene el resto en `/preguntas-frecuentes`.
- Política de Calidad no tenía enlace directo desde su declaración en HOME: corregido.
- Hero y pilares heredaban elementos demasiado grandes: branding más sobrio y proporciones compactas.
- El enlace activo del menú heredaba un color oscuro: corregido con cian sobre fondo oscuro.
- Pulsar el CTA durante la transición podía impedir el cierre del menú: se espera el evento de apertura antes de cerrarlo.
- La configuración declarada arrancaba Gunicorn sin ejecutar migraciones: se alinearon `render.yaml` y `Procfile` con `flask db upgrade && gunicorn app:app`.

Misión, Visión, ocho valores y la declaración de Calidad conservan los textos aprobados. Los cuatro pilares están fusionados en una sola sección. No hay otra galería de servicios en HOME. Los catálogos completos y datos administrativos permanecen intactos. Proyectos y testimonios se limitan a tres y solo se muestran cuando los filtros existentes proporcionan contenido publicable.

## Longitud y revisión visual

Se midió el HTML público capturado anteriormente, usando el mismo CSS de plataforma, frente al HOME Flask local:

| Ancho | Captura anterior | HOME local | Reducción |
|---|---:|---:|---:|
| 1440 px | 9246 px | 4123 px | 55,4 % |
| 390 px | 17312 px | 7345 px | 57,6 % |

Es una comparación orientativa: la base local de prueba no contiene los datos reales de producción y la altura cambiará con proyectos, fotografías o testimonios publicados. No representa una medición del servicio público actual. Se evitó fabricar contenido para llenar secciones vacías.

66 combinaciones de 11 rutas en 1920, 1440, 1366, 768, 390 y 375 px pasaron en Chrome. Se revisaron capturas de HOME, Nosotros, Contacto y Calidad. Sin scroll horizontal, IDs duplicados, formularios sin nombre accesible ni errores JavaScript. Se validaron Bootstrap, recursos, menú móvil, CTA durante apertura, movimiento reducido y navegación por teclado hasta el contenido.

## Rutas y contacto

Todas devuelven HTTP 200 en Flask local:

`/`, `/nosotros`, `/contacto`, `/politica-de-calidad`, `/privacy-policy`, `/terms-and-conditions`, `/servicios`, `/portafolio`, `/preguntas-frecuentes`, `/descargas`, `/descargas/programas`, `/descargas/manuales`, `/solicitar-servicio`.

Las páginas corporativas contienen identidad, enfoque, fundador y contacto. Calidad y Privacidad son independientes. El contenido aprobado de las dos páginas legales mantiene sus huellas SHA-256. No se creó ninguna política técnica ni ruta legal específica de Préstamos Enterprise sin aprobación.

Se verificaron los seis enlaces `mailto:` oficiales:

- info@afcybersolutions.com.do
- ventas@afcybersolutions.com.do
- cotizaciones@afcybersolutions.com.do
- soporte@afcybersolutions.com.do
- licencias@afcybersolutions.com.do
- a.felizv@afcybersolutions.com.do

HOME/footer usan principalmente información, ventas y soporte; Contacto y Nosotros conservan los seis departamentos. No se cambiaron SMTP, credenciales ni destinatarios internos.

Las cifras del perfil CEO se conservan en base de datos como única fuente numérica. Sus valores predeterminados no constituyen aprobación comercial: `metrics_verified` permanece desactivado y no se muestran cifras contradictorias. No se inventaron clientes, estadísticas, testimonios, certificaciones o proyectos.

No existe implementación de asistente virtual en este checkout; el botón de WhatsApp sí se conserva. Si producción utiliza un asistente externo, hace falta identificar su integración antes de incorporarlo aquí.

## Backend, seguridad y pruebas

25 pruebas automatizadas pasaron nuevamente con Flask 3.1.3 y las dependencias de `requirements.txt` en un directorio aislado. Cubren rutas públicas/admin, assets y enlaces internos, formularios, CSRF, validación, protección administrativa, contraseña de producción, descargas privadas, traversal, adjuntos, PDF/hash, OTP, vencimiento, firmas, versiones, correo simulado y compilación DDL de PostgreSQL.

Las cookies HttpOnly/SameSite, opción Secure en producción, sesiones, cabeceras de seguridad, handlers 404/500 y rollback existentes se conservaron. No se eliminaron medidas de seguridad. JavaScript pasó `node --check`.

`flask db upgrade` pasó sobre una base SQLite desechable; la revisión de migraciones existente no produjo cambios de esquema adicionales. No se ejecutaron migraciones contra PostgreSQL productivo. No se verificó Gunicorn en Linux ni el disco/SMTP reales de Render desde Windows.

`git diff --check` pasó. Git permanece en `main`, dos commits por delante de la referencia local `origin/main`, con modificaciones y archivos nuevos sin stage. No está limpio porque el trabajo se deja para revisión y también existen las eliminaciones ajenas mencionadas.

## Render y publicación pendiente

Build: `pip install -r requirements.txt`.

Start: `flask db upgrade && gunicorn app:app`.

Se conservan PostgreSQL, `AUTO_CREATE_DB=0`, contraseña administrativa segura, secretos en entorno, cookies Secure, SMTP requerido y `PRIVATE_STORAGE_ROOT` en disco persistente externo. No se leyeron ni expusieron valores secretos.

Antes de publicar se debe:

1. Revisar/selectivamente preparar el commit, incluyendo los nuevos templates y tests y separando las eliminaciones ajenas.
2. Contrastar en el panel de Render el comando real y la presencia de las variables requeridas, sin exponerlas.
3. Validar backup y migraciones en staging/PostgreSQL; comprobar almacenamiento persistente y SMTP reales.
4. Confirmar la fotografía, proyectos y testimonios reales configurados desde el panel; aprobar métricas si se quieren publicar.
5. Después del despliegue autorizado, comprobar en el dominio las rutas corporativas y legales y realizar la revisión funcional de descargas con sus permisos reales.

El proyecto queda listo para revisión y autorización de publicación. No se hizo push ni deploy ni se modificó la base de producción.
