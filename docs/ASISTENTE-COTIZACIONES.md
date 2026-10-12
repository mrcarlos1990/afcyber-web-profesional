# AFCyber Asistente Virtual y cotizaciones

Implementación local del 12 de octubre de 2026. Sin commit, push, despliegue ni cambios de producción. Estado actual: funcionalidad implementada y comprobada localmente; publicación condicionada a validar Render, PostgreSQL, SMTP y backups. Las instrucciones siguientes no autorizan operaciones remotas.

## Inspección y alcance

Se inspeccionaron estructura, Git, rutas Flask, modelos, plantillas públicas/administrativas, CSS/JS, tarjetas de productos, company.json, formularios, función SMTP y auditorías previas. No se encontró AGENTS.md aplicable en el proyecto. HEAD observado al comenzar: `90fb631`; los informes operativos no rastreados anteriores se preservaron y no forman parte de esta implementación.

Se conservan la identidad visual, logo, ilustraciones, retrato, responsive, descargas, solicitudes detalladas, documentos/firma/OTP, autenticación, CSRF y panel existentes. El antiguo formulario `/contact` acepta aún correo O teléfono y conserva los mensajes administrativos; ahora registra también la solicitud y su cola de correo. La nueva página `/cotizacion` exige correo Y teléfono. No se creó ninguna cuenta ni credencial de producción.

## Conocimiento y catálogo compartido

- `static/data/company.json`: datos institucionales, misión, visión, valores, calidad, contactos y hechos públicos de ubicación/fundador/teléfono. No se usaron métricas sin verificar, biografías privadas ni valores por defecto como horario publicado.
- `static/data/products.json`: fuente única de fichas comerciales para inicio, páginas de producto y chat. Extraída de las tarjetas reales anteriores, con campos explícitos y procedencia.
- `static/data/service-groups.json`: las tres categorías ya publicadas del inicio, compartidas por HOME y chat; mantienen sus mismas imágenes y textos.
- Servicios, FAQ y planes: consulta en vivo de los registros activos de sus modelos existentes. Los cambios del panel se reflejan sin otro catálogo de respuestas duplicado.
- Programas adicionales: únicamente registros de descargas publicados, activos y no eliminados, con archivo disponible o destino HTTPS. Se consultan desde el mismo modelo Program y no se incorporan borradores, rutas privadas, hashes, licencias internas o registros de clientes. Publicado para descarga no equivale automáticamente a disponible comercialmente.

El asistente devuelve campos públicos mediante una lista explícita, sin serializar modelos completos. No consulta mensajes, cotizaciones, usuarios, firmas, adjuntos, variables de entorno ni informes operativos para responder. Historia cronológica, horario, precios por producto, requisitos, módulos y licencias no publicados se indican como desconocidos, no se infieren.

Productos compartidos:

| Producto | Plataforma publicada | Funciones publicadas | Estado comercial |
|---|---|---|---|
| AFCyber Préstamos Enterprise | Android | Clientes/préstamos, cobros/pagos, intereses/mora/caja, recibos PDF, reportes/auditoría, importación/exportación | NO_CONFIRMADO |
| MultiNegocios | Windows | POS/créditos/servicios, reportes/dashboard, configuración/licencias, roles/permisos/auditoría, copias de seguridad, comprobantes | NO_CONFIRMADO |
| CMMS Empresarial | No publicada | Activos/mantenimiento, órdenes de trabajo e historial | NO_CONFIRMADO |

No hay capturas reales oficiales confirmadas para esos tres productos. Las tarjetas son tipográficas; no se reutilizan las ilustraciones de interfaces como capturas. Sistemas de ventas/facturación, inventario y clientes se explican mediante los servicios publicados POS/ERP y software empresarial; no se inventan nuevos productos independientes ni se atribuye inventario a MultiNegocios sin confirmación.

Estados admitidos en JSON: DISPONIBLE, EN_DESARROLLO, PROXIMAMENTE, NO_CONFIRMADO. Valores no reconocidos se tratan como NO_CONFIRMADO. Un estado más afirmativo requiere información verificada y revisión, no una inferencia por palabras clave.

Servicios incorporados: los ocho registros iniciales publicados (software empresarial, POS/ERP, web, ciberseguridad básica, CCTV/control de acceso, mantenimiento de computadoras, instalación de software, automatización) y las tres categorías del inicio. Redes e infraestructura se explican desde la categoría publicada del HOME. Se incorporan automáticamente otros servicios activos del panel. No se anuncian auditorías autorizadas, consultoría o reparación específica como servicios confirmados si no existen en las fuentes.

## Motor gratuito e interfaz

`assistant.py` implementa normalización de acentos y puntuación, sinónimos, palabras clave, coincidencia aproximada de términos distintivos, relevancia de servicios/FAQ y respuestas verificadas. No hay OpenAI API, LLM, suscripción ni servicio con cobro por conversación. Utiliza Python estándar, JSON y la base existente. El hosting y SMTP siguen siendo los ya configurados por el propietario; no se contrata ningún proveedor.

El contexto contiene como máximo dos identificadores de producto y caduca a los diez minutos. No se conserva un transcript del chat en base, archivos o localStorage. La cookie de sesión conserva identificadores públicos y los controles de la sesión, no preguntas completas.

El widget aparece en el layout público con bienvenida, nueve opciones, preguntas libres y botón Explorar productos. Cerrar, Escape y retorno de foco están implementados; no impone un modal que bloquee el resto de la web. El lanzador queda separado de WhatsApp y del botón superior; la cabecera del panel respeta el menú del sitio. Las comparaciones usan tabla en escritorio y filas apiladas con nombres de productos en móvil.

Las fichas muestran nombre, categoría, descripción, funciones, plataforma y estado. Enlaces Conocer más, Solicitar cotización y Hablar con un asesor. Las páginas reales están en `/productos/prestamos-enterprise`, `/productos/multinegocios` y `/productos/cmms-empresarial`.

La comparación presenta finalidad, negocio recomendado, plataforma, funciones, licencia y estado comercial, señalando campos no publicados. Las recomendaciones se basan en funciones reales y no garantizan compatibilidad. Una consulta sobre ferretería/ventas/inventario muestra MultiNegocios por su POS, aclarando que su inventario no está confirmado y que puede evaluarse POS/ERP o software a medida.

Preguntas sin evidencia reciben la respuesta de falta de información y enlaces de cotización/contacto. Solicitudes de secretos o contraseñas no producen información privada. Las categorías provienen de la misma fuente de productos, no de un catálogo paralelo.

## Cotizaciones persistentes y correo

`quotations.py` reutiliza normalización de correo, sesión, CSRF, formulario compartido y función SMTP de `app.py`.

1. Validación backend de nombre, producto/servicio, necesidad, contactos, presupuesto opcional y consentimiento. Mantiene compatibilidad con el formulario anterior.
2. Una transacción guarda `QuoteRequest`, su copia en ContactMessage y trabajos QuoteMail. La clave SHA-256 del nonce tiene restricción UNIQUE; dos envíos simultáneos no crean dos solicitudes.
3. El número `AFC-<año UTC>-<id con mínimo seis dígitos>` utiliza la PK de base generada por secuencia en PostgreSQL, sin leer MAX ni usar contadores en memoria. La secuencia global no se reinicia cada año. El identificador es estable y único; no es un token para consultar datos públicamente.
4. Se confirma el commit de solicitud y cola ANTES de intentar SMTP.
5. Cada trabajo se reclama mediante UPDATE condicional atómico y se confirma antes del envío: otro proceso/reintento no puede reclamarlo a la vez. Son únicos por solicitud y destinatario funcional (administrador/cliente).
6. Notificación a cotizaciones@afcybersolutions.com.do y confirmación al correo validado del cliente. El formulario anterior sin correo conserva solicitud y notificación administrativa, sin inventar destinatario del cliente.
7. HTML autoescapado y alternativa de texto, número/fecha/nombre/empresa/teléfono/correo/producto/necesidad/presupuesto. El administrador recibe Reply-To del cliente; From siempre procede de MAIL_DEFAULT_SENDER. El Message-ID es estable por trabajo.
8. La confirmación pública muestra el número y distingue guardado de entrega de correo. Nunca presenta una oferta/precio calculado sin datos comerciales verificados.

Solicitudes: RECIBIDA, EN_REVISION, RESPONDIDA, CERRADA. El fallo SMTP no cambia RECIBIDA ni pierde la solicitud.

Correo: PENDIENTE (incluye SMTP sin configurar), ENVIANDO, ENVIADO, FALLIDO (pendiente de reintento controlado), INCIERTO (timeout, desconexión o resultado ambiguo). Hasta cinco intentos efectivamente reclamados; sin transporte configurado no consume el límite. Los envíos de cotización no utilizan los reintentos internos rápidos de SMTP; las funciones antiguas conservan su comportamiento.

El panel `/admin/cotizaciones` presenta número, cliente, solución, fecha UTC, estado y correo; detalle, cambio de estado y reintentos protegidos por login, permiso administrativo y CSRF. No existen listados públicos ni rutas de consulta por número que expongan datos personales.

Comando para trabajos seguros pendientes/fallidos, dentro de un entorno autorizado ya migrado:

```text
flask --app app cotizaciones-reintentar --limit 20
```

No se configura ningún cron externo ni automatización remota. Un operador puede integrar ese comando con su proceso existente si lo autoriza. ENVIADO no se reenvía. INCIERTO requiere comprobación del proveedor y confirmación explícita en el panel. ENVIANDO tras un fallo de proceso se puede convertir a INCIERTO desde el panel después de cinco minutos, no reclamar automáticamente.

SMTP no proporciona entrega exactamente una vez: un servidor puede aceptar el mensaje y luego cortar la conexión. Ni un Message-ID estable obliga al proveedor a deduplicar. Los resultados ambiguos quedan retenidos para revisión y no se reenvían automáticamente; un reintento manual reconocido puede duplicar una entrega. SMTP aceptado no acredita recepción en bandeja de entrada.

## SMTP y seguridad

Variables existentes requeridas: MAIL_SERVER, MAIL_PORT (normalmente 587), MAIL_USE_TLS=1 para STARTTLS, MAIL_USERNAME y MAIL_PASSWORD cuando el proveedor las exija, MAIL_DEFAULT_SENDER con remitente aprobado. REQUIRE_SMTP=1 debe mantenerse en producción si ese es el control acordado. No se inventaron ni modificaron valores secretos; `.env.example` no cambió. La implementación reutiliza SMTP/STARTTLS existente; no introduce un proveedor nuevo ni configura SMTP_SSL/465 automáticamente.

Seguridad añadida: CSRF en chat y cotizaciones; mensajes hasta 600 caracteres y POST chat hasta 4096 bytes; cotizaciones hasta 20000 bytes con límites por campo; honeypot; escape Jinja y DOM creado con textContent; enlaces del chat limitados al origen; consultas parametrizadas; whitelist de estados; HMAC de identidad IP para rate limiting sin guardar IP en claro; buckets persistentes con actualizaciones atómicas y expiración; autenticación y permiso administrativo; errores de correo registrados en ámbito privado y log operativo sin cuerpos/credenciales.

Límites: 30 preguntas/minuto, 30 consultas de catálogo/minuto y cinco intentos nuevos de cotización/diez minutos por dirección de conexión. No se confía en X-Forwarded-For enviado por el visitante. En Render debe comprobarse si remote_addr identifica correctamente al cliente o a un proxy compartido; configurar una política de proxy confiable antes de cambiar esa confianza. Clientes detrás de NAT/proxy pueden compartir cuota. No almacenar consultas con información sensible; el widget lo recuerda.

La auditoría previa detectó Werkzeug 3.1.8 vulnerable en Windows/NTFS. Se actualizó el pin a 3.1.9 y el entorno local se volvió a validar; no se cambiaron otras dependencias. Los informes anteriores son historial y no representan este nuevo resultado.

## Migración pendiente y despliegue futuro

Nueva revisión: `20261012_0002`, después de `20260722_0001`. Crea quote_request, quote_mail y public_rate_bucket; no altera ni elimina tablas existentes. Usa checkfirst porque la baseline histórica crea metadata actual en bases vacías. Downgrade se detiene deliberadamente para evitar destruir solicitudes; no simula una restauración de datos.

Ensayo local en SQLite nueva y en otra con esquema anterior: upgrade/current/check aprobados en ambos escenarios, head nuevo y sin operaciones adicionales. La suite también compila DDL PostgreSQL, pero NO se hizo una conexión, ensayo ni migración PostgreSQL real.

Antes de publicar con autorización:

1. Revisar solamente `docs/ASISTENTE-COTIZACIONES-ARCHIVOS.txt`, preparar un commit selectivo y revisar staged. No mezclar informes operativos previos, scripts externos a esta implementación, bases ni backups.
2. Confirmar revisión desplegada, variables de producción, PostgreSQL/TLS, SMTP y disco persistente reales. Registrar backups de base y archivos y una restauración de prueba independiente. Mantener el procedimiento previo de migración de imágenes antes del redespliegue.
3. Ensayar la revisión nueva en un PostgreSQL independiente autorizado con snapshot del esquema anterior. Revisar el comando de Render: `flask db upgrade && gunicorn app:app` ejecutará la migración al arrancar y necesita autorización previa.
4. Autorizar separadamente commit/push/publicación y migración productiva. No se ejecuta ninguno en esta entrega. Revisar auto-deploy antes de un futuro push.
5. Tras migrar/publicar: validar chat, tipos de producto, formularios, login/panel, una entrega SMTP controlada autorizada a destinos de prueba, reintentos y privacidad. No enviar pruebas a clientes reales.
6. Comprobar que solicitudes, cola e imágenes sobreviven a reinicio y redespliegue real. La prueba de reiniciar Flask local no certifica Render.
7. Ante fallo, volver al código anterior sin borrar las tablas nuevas, filas ni disco. Las copias en ContactMessage permiten conservar el flujo anterior. Suspender nuevas solicitudes si no se puede confirmar el guardado; conservar la cola pendiente hasta restaurar una versión compatible. No ejecutar downgrade ni restaurar masivamente la base sin autorización: podría perder solicitudes/firma/documentos posteriores al backup.

Pendientes remotos: PostgreSQL real/concurrencia y permisos, migración productiva, SMTP real/recepción, identidad de proxy, dominio y revisión desplegada, persistencia de disco/base y recuperación. El dominio documentado sigue siendo https://afcybersolutions.com.do/; no se inventó URL de Render ni se infirió una caída desde el fallo de acceso anterior.

## Pruebas y evidencias

Suite completa final: 52 pruebas aprobadas, incluidas las 37 anteriores. Las 15 nuevas cubren empresa, productos/servicios, sinónimos, errores de escritura, contexto, desconocidos, fichas/categorías, comparación, recomendación prudente, borradores privados, validación/CSRF/rate limiting, identificadores, duplicados y concurrencia de dos escritores, persistencia al recrear Flask, HTML/From/Reply-To, SMTP simulado, fallos/reintentos/ambigüedad, CLI sin request y permisos/escape. Ninguna prueba envió correo real.

Navegador 1440×1000 y 390×844: apertura, cierre, Escape, fichas, comparación, categorías, respuestas desconocidas, enlace con servicio preseleccionado y formulario con número de solicitud. Sin errores JavaScript ni superposición del lanzador con WhatsApp. SMTP desactivado. Transporte de ensayo: Flask test_client persistente conectado al navegador mediante pipe local; sus redirects se siguieron en el bridge debido a las restricciones de loopback. Los tests backend validan los redirects HTTP reales.

Capturas `.verification/asistente-producto-escritorio.png`, `asistente-producto-movil.png`, `asistente-comparacion-escritorio.png`, `asistente-comparacion-movil.png`, `asistente-cotizacion-escritorio.png` y `asistente-cotizacion-movil.png`. Verificación: `.verification/assistant-browser-results.json`. Los screenshots y entornos se excluyen de Git.

Pip check: sin conflictos. Pip-audit de requirements actualizado: sin vulnerabilidades conocidas. JavaScript `node --check`: correcto. Diff whitespace: correcto. Versiones/códigos de salida y hashes de evidencia en `docs/ASISTENTE-COTIZACIONES-RESULTADOS.json`. No interpretar esos resultados como una garantía contra cualquier vulnerabilidad o como comprobación remota.

## Archivos y mantenimiento

Creados: assistant.py, quotations.py, JSON de productos y categorías, CSS/JS/widget, páginas de producto/cotización, plantillas administrativas y correo, migración, pruebas nuevas y estos informes/manifiesto. Modificados: app.py, models.py, requirements.txt, company.json, layouts público/admin, HOME, tarjetas y formulario compartidos, README.

Editar company.json y products.json con información pública confirmada; las categorías del inicio en service-groups.json. Revisión por administrador/desarrollador, pruebas y publicación posterior según el proceso del repositorio. Servicios, FAQ y programas se administran desde el panel existente; activar/publicar registros hace pública su información. No hay endpoint público para escribir conocimiento. Los campos no confirmados deben seguir vacíos/NO_CONFIRMADO y las imágenes deben corresponder a archivos reales aprobados. No almacenar secretos o datos de clientes en los JSON públicos.

Git mantiene modificaciones sin commit y los archivos nuevos de esta función, más los informes anteriores no rastreados que ya existían. El índice continúa vacío; no se hizo commit, push ni despliegue.
