# Preparación final para producción — AFCyber Solutions

## Conclusión

El código local y los recursos están preparados para un commit selectivo y revisión. El índice Git se prepara selectivamente en la verificación final; no se crea commit, push ni deploy. No se consultó ni modificó la base de producción. No se puede confirmar el estado real de las variables, disco, migraciones o revisión publicada en Render sin acceso a ese servicio.

## Referencias Git y alcance

main contiene dos commits locales sobre la referencia disponible origin/main: 45bbdbf (Rediseño corporativo AFCyber Solutions) y 1e8f55d (Agregar estructura corporativa y secciones legales). Esta referencia remota local no demuestra cuál fue la última publicación; no se hizo fetch ni se verificó la revisión desplegada.

El rediseño Flask está presente tanto en esos commits como en modificaciones sin commit. GET / utiliza templates/public/index.html y public/base.html. Los HTML raíz y Netlify pertenecen al despliegue anterior; no forman parte del arranque Flask.

Hay 14 archivos rastreados modificados desde HEAD, archivos nuevos y diez eliminaciones ajenas de imágenes raíz. Estas eliminaciones no se revierten y se dejan fuera de la selección propuesta, pendientes de la tarea que las originó. No utilizar git add -A para este paquete.

## Archivos del próximo commit

La lista exacta está en docs/ARCHIVOS-PROXIMO-COMMIT.txt. Incluye:

- Procfile, render.yaml, README.md, app.py y nota legacy en scripts/build_corporate.py.
- static/css/home.css, static/js/platform.js y nuevo static/css/corporate-images.css.
- Plantillas públicas modificadas: base, catalog, contact, index, quality, founder-profile e identity.
- Nuevos componentes corporate-images y FAQ, y página pública FAQ.
- 42 WebP de static/images/corporativas, incluidos Hero, Cloud y recursos reservados.
- scripts/optimize_corporate_images.py, tres archivos de pruebas y documentación.
- Los 14 originales seleccionados por el inventario, para que optimizador y comprobaciones de integridad puedan reproducirse tras clonar. Los dos originales alternativos no utilizados quedan fuera.

Los originales son imágenes corporativas aprobadas, no almacenamiento de clientes. Si se decide excluir todos los originales del repositorio, primero debe ajustarse el flujo de pruebas: test_corporate_images comprueba sus hashes y requiere esas fuentes. No excluirlos dejando una suite que falla en un checkout nuevo.

## Recursos Git

Los 42 WebP existen y no están ignorados; se incorporan selectivamente al índice durante la verificación final, junto con todos los componentes y estilos nuevos. También deben incluirse el nuevo CSS, los componentes Jinja y static/data/company.json, que ya pertenece al commit corporativo local.

## Seguridad

El análisis de los 117 archivos candidatos frente a origin/main y archivos nuevos no encontró patrones de claves privadas, tokens GitHub/AWS, URLs con contraseña o secretos asignados. No se imprimieron valores potencialmente sensibles. Esta revisión de patrones y cambios no sustituye una garantía absoluta frente a cualquier formato de secreto.

No hay .env real, base de datos, APK, PDF privado, claves o almacenamiento privado rastreados en las categorías revisadas; solo .env.example. .gitignore protege entornos, .env, bases, storage/private/uploads, documentos, logs e instaladores. .verification está excluido. Ninguno de esos directorios entra en la lista del commit.

Se conservan validación de ADMIN_PASSWORD, SECRET_KEY, PostgreSQL, sesiones seguras, CSRF, autenticación y protección de archivos privados. No se han cambiado direcciones SMTP ni credenciales.

## Render y dependencias

Procfile: web: flask db upgrade && gunicorn app:app
render.yaml: buildCommand pip install -r requirements.txt; startCommand flask db upgrade && gunicorn app:app.

requirements.txt permanece intacto. Incluye Flask 3.1.3, Werkzeug 3.1.8, Flask-SQLAlchemy, Flask-Migrate, Alembic, Gunicorn, psycopg y librerías existentes. Pillow está disponible por las dependencias de imágenes existentes; no se añadió dependencia de producto.

El arranque carga app:app y las rutas Flask canónicas. El código reconoce comandos de migración para evitar exigir el esquema antes de flask db upgrade. Render configura PostgreSQL mediante DATABASE_URL, almacenamiento persistente /var/data/afcyber-storage, FLASK_DEBUG=0, AUTO_CREATE_DB=0 y cookies seguras. No se ejecuta el generador HTML legacy.

## Migraciones y pruebas

Existe una única revisión: 20260722_0001, sin archivos de migración nuevos en estos cambios. En una nueva SQLite desechable se ejecutaron heads, upgrade, current y check: todos terminaron correctamente. current alcanzó 20260722_0001; check informó No new upgrade operations detected. La base y almacenamiento usados están dentro de .verification, excluidos de Git.

Se repitió la suite completa: 30 pruebas aprobadas. Incluye compilación DDL PostgreSQL, controles de producción, rutas, templates, enlaces, assets, formularios/CSRF, permisos, descargas y funciones administrativas. No se realizó una migración contra PostgreSQL real ni una prueba de Gunicorn en Render. La revisión visual previa de 66 combinaciones responsive permanece documentada; no se cambió diseño en esta fase.

git diff --check correcto; las advertencias LF/CRLF reflejan conversión de finales de línea, no errores de whitespace. El working tree conserva cambios sin commit y eliminaciones ajenas; no está limpio.

## Riesgos antes de publicar

1. Omitir nuevos templates o company.json puede provocar errores de importación/Jinja y HTTP 500; omitir CSS/WebP provoca 404. Publicar ambos commits corporativos y todo el paquete selectivo.
2. Variables reales de Render pendientes de contraste: SECRET_KEY seguro, ADMIN_PASSWORD seguro, DATABASE_URL PostgreSQL, BASE_URL HTTPS, PRIVATE_STORAGE_ROOT persistente y SMTP. Con REQUIRE_SMTP=1, MAIL_SERVER y MAIL_DEFAULT_SENDER son obligatorios. Su ausencia detiene el arranque deliberadamente.
3. Migración real pendiente de verificación en el despliegue autorizado: permisos, conexión, estado de Alembic y esquema pueden diferir de la base desechable. Tomar las medidas operativas habituales antes de ejecutar upgrade en producción.
4. Disco privado debe estar montado y ser escribible. No publicar APK privados ni sustituir ese almacenamiento por static.
5. Las diez eliminaciones de imágenes raíz pueden afectar el despliegue estático antiguo; no se mezclan con esta propuesta. Las rutas Flask fueron comprobadas.
6. Cloud sigue reservado porque el catálogo local no declara ese servicio; no se creó contenido comercial. No es un fallo 404.
7. Bootstrap y Font Awesome utilizan CDN existentes; su disponibilidad externa afecta estilo/interacciones y no se garantiza mediante pruebas locales.
8. SQLAlchemy emite un aviso existente por Query.get legacy, sin fallos en pruebas.

Detener aquí. Publicación únicamente tras autorización expresa.

## Verificación final del índice y comprobaciones manuales Render

Selección final: 86 archivos, de los cuales 42 son WebP. Se revisaron nombres exactos respetando mayúsculas/minúsculas en el sistema de archivos y las referencias literales de assets y templates. Las referencias dinámicas de imágenes y páginas se validan mediante las pruebas de renderizado y recursos. No se detectaron dependencias omitidas. Esto valida rutas para Linux; no constituye una ejecución real de Gunicorn sobre Linux.

La suite completa volvió a pasar: 30 pruebas. Se prepara exclusivamente la lista docs/ARCHIVOS-PROXIMO-COMMIT.txt, sin git add -A ni git add .; las diez eliminaciones ajenas no se incluyen. Los dos originales alternativos no usados permanecen sin rastrear. Se comprueban git diff --check y git diff --cached --check.

No existe un conector Render disponible ni se verificó acceso autenticado a su panel. No se abrió ninguna conexión PostgreSQL real. Estado remoto del servicio, PostgreSQL, migraciones, disco y respaldos: no verificado.

Antes de autorizar la publicación, realizar manualmente:

1. Render Dashboard → servicio web: confirmar repositorio/branch main, runtime Python, build pip install -r requirements.txt y start flask db upgrade && gunicorn app:app. Confirmar que no existe otro comando configurado en el panel que sustituya al Blueprint.
2. Environment: comprobar presencia de SECRET_KEY seguro, ADMIN_PASSWORD seguro, DATABASE_URL PostgreSQL, BASE_URL=https://afcybersolutions.com.do, PRIVATE_STORAGE_ROOT=/var/data/afcyber-storage y SIGNING_SECRET. FLASK_DEBUG=0, AUTO_CREATE_DB=0, SESSION_COOKIE_SECURE=1, STORAGE_PROVIDER=render_disk y REQUIRE_SMTP=1. Comprobar MAIL_SERVER y MAIL_DEFAULT_SENDER, además de MAIL_USERNAME/MAIL_PASSWORD si el proveedor requiere autenticación. No copiar valores secretos al chat o al informe.
3. PostgreSQL → conexión y permisos: confirmar base vinculada, disponibilidad y acceso del usuario de la aplicación. En una sesión SQL de lectura autorizada ejecutar SELECT 1; no publicar la URL de conexión ni credenciales.
4. Esquema real: consultar SELECT version_num FROM alembic_version; o usar flask db current desde la shell configurada. La revisión esperada es 20260722_0001. Registrar el resultado; no ejecutar upgrade todavía. Si la tabla no existe o la revisión difiere, revisar antes de publicar.
5. Disk del servicio: confirmar montaje /var/data/afcyber-storage. En shell comprobar test -d "$PRIVATE_STORAGE_ROOT" y test -w "$PRIVATE_STORAGE_ROOT" sin escribir archivos. Confirmar que los adjuntos, APK y documentos privados existentes siguen en ese almacenamiento, fuera de static y del repositorio.
6. Respaldo recuperable: comprobar en el proveedor PostgreSQL la disponibilidad real del backup o recuperación puntual, su fecha, retención y procedimiento de restauración. Confirmar una restauración de prueba en un destino aislado si está disponible. Resguardar también el almacenamiento privado mediante el procedimiento autorizado del servicio; una copia de PostgreSQL por sí sola no contiene los APK y documentos del disco. No asumir que los respaldos están habilitados por defecto.
7. Revisar logs de arranque actuales sin compartir secretos; resolver errores de conexión, esquema, SMTP o permisos. Documentar revisión desplegada y respaldo aprobado antes de permitir migraciones o publicación.

Recomendación: autorizar el commit cuando se revise la selección preparada. Mantener despliegue y push detenidos hasta confirmar manualmente las condiciones remotas, especialmente respaldo recuperable, variables y almacenamiento. No hay autorización de publicación en esta tarea.
