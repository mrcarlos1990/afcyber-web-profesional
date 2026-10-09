# Actualización corporativa — AFCyber Solutions

6 de octubre de 2026.

## Estado de integración

La actualización corporativa está implementada y probada en la copia de revisión `.verification/corporate-candidate`. Durante el trabajo se inició externamente `git pull --rebase origin main`, que cambió el proyecto a la versión de producción y dejó conflictos en `.gitignore`, `static/js/platform.js`, `templates/public/base.html` y `templates/public/index.html`.

Para no interferir con esa operación mientras se determina quién la finalizará, la integración con producción se preparó y verificó en una copia aislada. La carpeta principal todavía contiene los conflictos del rebase. Este informe no afirma que la integración esté terminada ni que los cambios se hayan publicado.

## Auditoría actualizada

La inspección inicial encontró las entradas estática de Netlify y Flask/Render, formularios de contacto, administración, servicios, planes, portafolio y perfiles institucionales. Los únicos correos públicos configurados eran `info@afcybersolutions.com.do`; el correo `admin@afcybersolutions.com.do` pertenece a autenticación y no se sustituyó por un contacto comercial.

Después del cambio de Git apareció el backend de producción, que contiene también descargas privadas, manuales, solicitudes de servicio, adjuntos, documentos, generación de PDF, OTP, firmas, trazabilidad y envío SMTP. La integración preparada conserva ese backend y sus filtros de proyectos/testimonios/redes públicas. No se reemplazó con la versión simple ni se alteraron endpoints POST, modelos, migraciones o almacenamiento.

Existen bases locales de dos arquitecturas distintas; se inspeccionaron únicamente datos institucionales mediante lectura. Las pruebas usaron SQLite en memoria y almacenamiento temporal. No se actualizaron registros reales ni credenciales.

## Contenido y diseño preparados

- Una fuente de contenido oficial: `static/data/company.json`, con los textos de Quiénes somos, Misión, Visión, valores, Política de Calidad y seis correos proporcionados por el usuario.
- HOME: identidad antes de Por qué AFCyber; Misión y Visión en dos columnas, ocho valores en una lista compacta y Calidad como declaración institucional. El fundador permanece separado después de los pilares.
- Contacto del HOME: cinco departamentos compactos. Dirección/CEO solo en páginas internas.
- Footer: cuatro columnas (AFCyber, Empresa, Servicios, Contacto), tres correos, WhatsApp, acceso a todos los contactos y enlaces legales.
- `/nosotros`: Quiénes somos, Misión, Visión, valores, Calidad, enfoque, fundador y contactos institucionales.
- `/contacto`: seis departamentos con enlaces `mailto:`, teléfono, dominio y formulario compatible con el backend existente.
- `/politica-de-calidad`: declaración oficial, principios, compromiso con el cliente, seguridad de la información, mejora continua y contacto.
- FAQ dentro de un desplegable de Contacto, conservando sus preguntas para compensar el espacio de la identidad.
- Métricas y testimonios genéricos precargados no se muestran como hechos verificados. Los registros siguen existiendo; la integración con producción reutiliza su selección de testimonios públicos.
- Proyectos del HOME Flask y del catálogo usan los filtros existentes de producción. Si no hay proyectos reales publicados, no se inventan tarjetas para rellenar la sección.
- Estilos y animaciones breves, focus visible, movimiento reducido y soporte de móvil sin desbordamiento horizontal.

En la copia estática, el HOME a 1440 px pasó de 4835 px del rediseño anterior a 5161 px con toda la identidad y los departamentos: aproximadamente 326 px adicionales (6,7 %). Sigue siendo aproximadamente un 39 % más corto que el HOME original estático de 8480 px. A 390 px, la identidad completa incrementa la altura respecto del rediseño anterior en unos 671 px; el contenido se apila sin letras excesivamente pequeñas.

## Políticas generales aprobadas

El usuario confirmó estas fuentes:

- `https://afcybersolutions.com.do/privacy-policy`
- `https://afcybersolutions.com.do/terms-and-conditions`

Ambas respondieron HTTP 200. Se extrajo literalmente el `<main>` de cada documento, sin importar scripts remotos ni redactar nuevas condiciones. Sus huellas SHA-256 quedan en `templates/public/legal/sources.json`; las pruebas comparan el contenido servido por Flask y por las páginas estáticas con esas huellas originales.

Las rutas generales siguen siendo `/privacy-policy` y `/terms-and-conditions`, públicas sin login. Calidad es un documento distinto en `/politica-de-calidad`. Las reglas específicas de Netlify van antes de su fallback, para que las rutas limpias sirvan sus archivos y no el HOME.

La política publicada menciona controles antiabuso y Turnstile; la integración no añade ni afirma funciones nuevas para cumplir ese texto. Debe revisarse la correspondencia entre el despliegue real y el documento vigente por separado, manteniendo intactas sus declaraciones durante este trabajo.

## Préstamos Enterprise

No se crearon páginas, rutas activas, documentos ni afirmaciones sobre datos de la aplicación. Las propuestas están en `docs/LEGAL-PRESTAMOS-PROPUESTA.md`:

- `/apps/afcyber-prestamos-enterprise/privacy-policy`
- `/apps/afcyber-prestamos-enterprise/terms-and-conditions`
- `/apps/afcyber-prestamos-enterprise/support`
- `/apps/afcyber-prestamos-enterprise/data-deletion` — solo si corresponde al funcionamiento real.

No se encontraron fuentes Android ni una implementación de cuentas/datos de la app. El login administrativo del sitio no se considera evidencia sobre las cuentas de Préstamos Enterprise.

## Archivos involucrados en la integración preparada

Flask:

- `app.py`: contenido corporativo en el contexto; nuevas vistas GET públicas; catálogos y sitemap; conserva el backend de producción.
- `templates/public/base.html`: CSS corporativo, títulos de páginas y canonical correctos, conservando SEO, JSON-LD, analytics y enlace para saltar al contenido.
- `templates/public/index.html`, `catalog.html`, `about.html`, `contact.html`, `quality.html`, `legal.html`.
- Parciales públicos de navegación, footer, identidad, departamentos, enfoque, fundador, formulario, botones flotantes e imágenes de proyectos.
- `templates/public/legal/privacy-policy.html`, `terms-and-conditions.html`, `sources.json`.

Estático y compartido:

- `index.html`, `nosotros.html`, `servicios.html`, `portafolio.html`, `contacto.html`, `politica-de-calidad.html`, `privacy-policy.html`, `terms-and-conditions.html`.
- `static/css/corporate.css`, `static/data/company.json`.
- `static/js/main.js`: conserva el mensaje de WhatsApp e incluye empresa opcional; mejora la activación de animaciones para evitar contenido invisible si AOS no inicia.
- `static/js/platform.js`: conserva el script de producción y evita declarar dos veces las variables del menú.
- `scripts/build_corporate.py`: regenera los componentes y páginas estáticas desde los mismos textos y templates de Flask; usa Jinja2, ya incluido por Flask.
- `netlify.toml`: correspondencia de URLs limpias con archivos existentes.
- `.gitignore`: conserva las exclusiones de producción y excluye verificación local.
- `tests/test_corporate.py` y estos informes.

## Verificación de la copia de revisión

- 20 pruebas de backend: las 13 existentes y siete de contratos corporativos. Todas pasan.
- Rutas públicas, un H1, seis correos oficiales, separación de Calidad y Privacidad y conservación literal de los documentos legales.
- CSRF rechaza contactos sin token; validación de campos; persistencia de empresa/correo/servicio; panel protegido.
- Descargas privadas, registro de eventos, solicitudes, adjuntos, PDF, hashes, firmas, OTP, vencimiento y versiones de documentos.
- 56 comprobaciones de páginas/tamaños en Chrome para las versiones estática y Flask: HOME en ocho tamaños entre 360 y 1920 px; Nosotros, Contacto, Calidad y las dos páginas legales en escritorio, tablet y móvil.
- Sin scroll horizontal ni IDs repetidos; labels en formularios; navegación, `mailto:`, FAQ y movimiento reducido.
- Mensajes de WhatsApp interceptados durante las pruebas, sin enviar mensajes reales.
- Capturas y resultado detallado en `.verification/corporate-responsive.json`.

## Pendientes

Finalizar la integración del rebase en la carpeta principal después de aclarar quién la ejecutará. Confirmar datos reales antes de activar métricas o testimonios; completar proyectos reales desde el panel. Aprobar las rutas propuestas de la aplicación y confirmar su funcionamiento antes de redactar políticas específicas. No se realizó publicación ni push.
