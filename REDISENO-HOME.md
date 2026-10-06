# Rediseño del HOME de AFCyber Solutions

Implementado el 6 de octubre de 2026, sobre el proyecto existente. Cambios locales; no se realizó publicación, push ni modificación de la base de datos de producción.

## Auditoría y arquitectura

El repositorio contiene dos entradas públicas independientes:

- Netlify: `index.html`, `static/css/style.css`, `static/js/main.js`; `netlify.toml` publica la raíz.
- Flask/Render: `app.py`, `templates/public/index.html`, `templates/public/base.html`, `static/css/platform.css`, `static/js/platform.js`; `render.yaml` y `Procfile` usan Gunicorn.

Las dos entradas utilizan Bootstrap 5 y Font Awesome por CDN. La estática usa AOS. Flask administra la configuración, contenido y contactos con SQLAlchemy y SQLite por defecto, admite otra URL de base de datos y protege el panel con Flask-Login. El panel incluye configuración, Hero, empresa, fundador, servicios, planes, portafolio, testimonios, FAQ, redes, mensajes y usuarios. Las cargas de imágenes y CV permanecen en `static/uploads`.

El formulario Flask publica en `/contact`; exige `name`, `phone`, `message`, y admite `company`, `email`, `requested_service`. La protección CSRF propia verifica `_csrf_token`. La versión estática convierte el contacto en un mensaje de WhatsApp; no tenía persistencia ni envío de correo.

Los scripts dependen de `mainNav`, `menu` o `navbarMenu`, `year` o `currentYear`, `topButton` o `backToTop`, `contactForm`, `.js-wa` o `.js-whatsapp`, `.reveal`, `[data-counter]` y los IDs del FAQ. Se conservaron los IDs funcionales y se añadieron alias para enlaces anteriores a planes y fundador. El canvas era independiente y se retiró de los HOME para evitar animación continua.

El HOME Flask reutilizaba el layout y el parcial de alertas; sus secciones eran independientes. El rediseño añade parciales compartidos de navegación, footer e imágenes de proyectos. Las páginas administrativas conservan sus templates y estilos originales.

No se encontraron archivos fuente de asistente virtual, endpoints de chat, páginas legales, sitemap, robots, canonical, datos estructurados ni un sistema separado de cotizaciones. Tampoco había una galería independiente ni una sección adicional de confianza corporativa en estas entradas. No se eliminó ninguno de esos elementos. Analytics y Search Console existentes en Flask se conservan. No existe una fotografía identificable del fundador entre las imágenes originales; se usa la foto configurada si existe, o la identidad de la empresa.

## Plan aplicado y cambios

- Conservar framework, base de datos, configuración de branding, imágenes originales, SEO y rutas existentes.
- Hero con el título y texto solicitados, CTA de cotización y acceso a servicios; altura, tipografía y proporciones controladas.
- Una sección de seis categorías en tres columnas y dos filas en escritorio. Las categorías son resúmenes de presentación; el catálogo conserva todos los registros administrables de servicios y sus precios.
- Tres proyectos existentes en la portada. El catálogo mantiene el resto y las URLs de los proyectos; cuando no existe enlace externo se accede a su tarjeta interna.
- Cuatro pilares compactos de confianza en una fila de escritorio.
- Empresa y fundador agrupados en dos columnas. Historia, misión, visión, valores, biografía, experiencia, habilidades, LinkedIn y CV existentes permanecen accesibles en la página interna Flask.
- Tres testimonios existentes; no se añadieron nombres, comentarios ni estrellas. Los testimonios de origen son genéricos y deben validarse antes de presentarlos como referencias reales.
- Tres FAQ iniciales y acceso desplegable a los demás, sin borrar preguntas.
- Formulario con labels visibles, teléfono, servicio y mensaje; correo y empresa opcionales en un desplegable. CSRF también se incluye directamente en el HTML Flask, para no depender de JavaScript.
- Footer más compacto, logo oficial, contactos configurados, enlaces internos y año dinámico. No se muestran redes que solo tienen `#` como URL. No se inventaron enlaces legales.
- CSS compartido y acotado a `.compact-site`, espaciado consistente, focus visible, soporte de movimiento reducido y menú móvil que se cierra al seleccionar enlaces.
- Versiones WebP optimizadas del logo y dos imágenes existentes; los originales permanecen intactos. Carga diferida fuera del Hero; no se agregaron dependencias al producto.

## Secciones fusionadas y retiradas solamente del HOME

Se unieron Nosotros y fundador en Flask, y se redujo Por qué elegir a cuatro pilares en la versión estática. El portafolio se presenta una sola vez con tres tarjetas.

Planes completos, tarjetas adicionales de servicios y proyectos, misión/visión/valores, biografía repetida, timeline y nube de habilidades dejan de ocupar espacio en la portada. Están disponibles en los catálogos internos. El FAQ adicional queda dentro de un desplegable.

Las estadísticas ambiguas de la portada estática —porcentaje de enfoque en calidad y cifra de soporte sin unidad clara— se sustituyeron por una franja descriptiva sin números. Flask muestra las cuatro métricas ya configuradas en el perfil del fundador en una sola franja. No se modificaron sus valores ni se interpretaron como cifras verificadas.

## Archivos modificados

- `.gitignore`: excluye archivos y dependencias de verificación local.
- `app.py`: únicamente tres rutas públicas GET para `/servicios`, `/portafolio` y `/nosotros`, reutilizando los modelos existentes.
- `index.html`: HOME estático.
- `static/js/main.js`: menú, movimiento reducido y servicio solicitado en el mensaje de WhatsApp.
- `static/js/platform.js`: menú móvil y movimiento reducido.
- `templates/public/base.html`: incluye la hoja visual compartida y su clase de alcance.
- `templates/public/index.html`: HOME Flask.

Archivos añadidos:

- `static/css/home.css`.
- `servicios.html`, `portafolio.html`, `nosotros.html`.
- `templates/public/catalog.html`.
- `templates/public/partials/nav.html`, `footer.html`, `project-image.html`.
- `static/img/brand.webp`, `barber.webp`, `pos.webp`.
- Este informe.

No se modificaron `models.py`, las vistas administrativas, el endpoint `/contact`, la autenticación, las cargas de archivos, los requisitos del proyecto ni la configuración de despliegue.

## Verificación

Pruebas Flask con una base SQLite en memoria, independiente de la base existente:

- HOME, servicios, portafolio, nosotros y login responden HTTP 200.
- Acceso al panel sin autenticar redirige al login.
- Envío de contacto sin token CSRF devuelve HTTP 400.
- Envío válido persiste nombre, teléfono, mensaje y servicio.
- Envío sin un campo obligatorio no crea un registro adicional.

Revisión en Chrome de las dos versiones a 1920×1080, 1440×900, 1366×768, 1024×768, 768×1024, 430×932, 390×844 y 360×800:

- Sin scroll horizontal en los tamaños comprobados.
- Un H1 por HOME; enlaces de sección válidos.
- Menú móvil abre y cierra; catálogos públicos accesibles.
- FAQ adicional despliega correctamente.
- Formulario estático genera el WhatsApp oficial e incluye el servicio. La apertura se interceptó: no se enviaron mensajes reales.
- Movimiento reducido sin canvas continuo; sin errores JavaScript en la revisión.
- Inspección visual de capturas completas en escritorio y móvil.
- Sintaxis de ambos JavaScript y revisión del diff sin errores de espacios.

Comparación de altura de la versión estática original y nueva en el mismo navegador:

| Tamaño | Antes | Después | Reducción |
| --- | ---: | ---: | ---: |
| 1920×1080 | 8660 px | 4842 px | 44 % |
| 1440×900 | 8480 px | 4835 px | 43 % |
| 1366×768 | 8609 px | 4868 px | 43 % |
| 1024×768 | 9382 px | 4871 px | 48 % |
| 768×1024 | 14246 px | 6212 px | 56 % |
| 430×932 | 16715 px | 8327 px | 50 % |
| 390×844 | 16913 px | 8562 px | 49 % |
| 360×800 | 17425 px | 8760 px | 50 % |

La versión Flask se comprobó con el contenido inicial del proyecto. La longitud final dependerá de los textos e imágenes configurados en cada instalación. No se verificaron envío real de WhatsApp, entrega de correo, DNS, producción ni todos los flujos administrativos; sus implementaciones no se modificaron.

## Problemas encontrados y recomendaciones pendientes

1. Confirmar métricas y testimonios precargados: existen en el proyecto, pero no hay evidencia de que sean referencias verificadas.
2. Configurar las URLs reales de las redes desde el panel; actualmente las iniciales son placeholders.
3. Incorporar la fotografía oficial del fundador mediante el campo existente del panel.
4. Si el sitio publicado tiene asistente o páginas legales, recuperar sus fuentes oficiales antes de integrarlas. No estaban en este checkout y no se inventaron sustitutos.
5. Completar imágenes y URLs reales de cada proyecto desde el panel. Las imágenes reutilizadas son material promocional existente; los proyectos sin imagen mantienen una alternativa visual neutra.
6. La climatización tiene material original y figura en la portada solicitada; en Flask conviene agregar su ficha administrable al catálogo si aún no está registrada.
7. Ambas versiones siguen coexistiendo. Render usa Flask y Netlify usa el HTML estático; conviene elegir una como fuente editorial a largo plazo para evitar divergencias de contenido.
