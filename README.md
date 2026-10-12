# AFCyber Solutions Platform

Plataforma Flask para el sitio corporativo de AFCyber Solutions con panel administrativo, descargas controladas, solicitudes de servicio, documentos PDF y firma electronica con trazabilidad tecnica.

## Tecnologias

- Flask, Flask-SQLAlchemy, Flask-Login y Flask-WTF.
- SQLite solo para desarrollo.
- PostgreSQL en produccion mediante `DATABASE_URL`.
- Flask-Migrate/Alembic para migraciones.
- ReportLab + QR para PDF profesional verificable.
- SMTP configurable con reintentos limitados y registro de entrega.

## Instalacion local

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python app.py
```

URLs locales:

- Web publica: `http://127.0.0.1:5000`
- Panel admin: `http://127.0.0.1:5000/admin/login`
- Descargas: `http://127.0.0.1:5000/descargas`
- Solicitar servicio: `http://127.0.0.1:5000/solicitar-servicio`

## Variables

Desarrollo:

```env
SECRET_KEY=replace-with-a-random-secret-of-at-least-32-characters
SIGNING_SECRET=replace-with-a-random-signing-secret
DATABASE_URL=sqlite:///instance/afcyber_platform.db
ADMIN_EMAIL=admin@afcybersolutions.com.do
ADMIN_PASSWORD=replace-with-a-strong-initial-admin-password
FLASK_DEBUG=1
AUTO_CREATE_DB=1
SESSION_COOKIE_SECURE=0
BASE_URL=http://127.0.0.1:5000
PRIVATE_STORAGE_ROOT=storage
REQUIRE_SMTP=0
```

Produccion:

```env
SECRET_KEY=<GENERAR_CLAVE_ALEATORIA_SEGURA>
SIGNING_SECRET=otra-clave-aleatoria-para-tokens-y-hashes
DATABASE_URL=postgresql://...
ADMIN_EMAIL=admin@afcybersolutions.com.do
ADMIN_PASSWORD=<CONFIGURAR_CONTRASENA_INICIAL_SEGURA>
FLASK_DEBUG=0
AUTO_CREATE_DB=0
SESSION_COOKIE_SECURE=1
BASE_URL=https://afcybersolutions.com.do
PRIVATE_STORAGE_ROOT=/var/data/afcyber-storage
REQUIRE_SMTP=1
```

Correo:

```env
MAIL_SERVER=
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=
MAIL_MAX_RETRIES=2
COMPANY_NOTIFICATION_EMAIL=info@afcybersolutions.com.do
SALES_EMAIL=
SUPPORT_EMAIL=
```

Almacenamiento privado:

```env
STORAGE_PROVIDER=render_disk
PRIVATE_STORAGE_ROOT=/var/data/afcyber-storage
MAX_UPLOAD_MB=60
S3_ENDPOINT_URL=
S3_BUCKET=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
```

## Descargas y documentos

Los instaladores, manuales, documentos privados, PDFs firmados y adjuntos se guardan bajo `PRIVATE_STORAGE_ROOT`, fuera de `static/` y fuera de Git. En desarrollo puede ser `storage/`; en Render debe ser un disco persistente como `/var/data/afcyber-storage`.

Las imágenes públicas y CV cargados desde el panel se guardan en
`PRIVATE_STORAGE_ROOT/public-media`, una carpeta pública separada de los
documentos privados. `/media/<archivo>` sirve únicamente esos recursos; las
rutas anteriores `/static/uploads/<archivo>` siguen siendo compatibles.
Las imágenes JPG/PNG/WebP se convierten a WebP, hasta 1920 px, conservando
proporción y transparencia. ICO y PDF conservan su formato.
Antes de un despliegue futuro, copiar las cargas públicas existentes de
`static/uploads` al directorio `public-media` del disco persistente, conservando
sus nombres, y comprobar el montaje real del servicio. El respaldo local de
`static/uploads` mantiene acceso a archivos anteriores mientras existan en el
checkout, pero no garantiza que sobrevivan a un despliegue de Render.

Formatos permitidos:

- Programas: `.exe`, `.msi`, `.zip`
- Manuales: `.pdf`
- Adjuntos: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.webp`, `.zip`

## Firma electronica

La firma por token usa token aleatorio hasheado, OTP hasheado, vencimiento, limite de intentos, consentimiento, hash de IP/User-Agent, hash del documento, hash firmado y auditoria. La firma del representante AFCyber requiere sesion administrativa y OTP enviado al correo del administrador.

Si un documento firmado se modifica, el sistema crea una nueva version, invalida solicitudes pendientes anteriores y exige nuevas firmas para la version vigente.

## PDF y verificacion

Cada documento genera un PDF privado en `signed-pdfs/` dentro de `PRIVATE_STORAGE_ROOT`. El PDF incluye numero de documento, hash SHA-256, QR grafico de verificacion, firmas de la version vigente y auditoria tecnica.

La pagina `/verificar-documento/<codigo>` muestra informacion minima: codigo, tipo, estado, fecha, firmantes y hash. No expone el contenido completo ni datos personales innecesarios.

## Arquitectura publica y Render

Render sirve `GET /` mediante `app.py:index`, que renderiza
`templates/public/index.html` y hereda `templates/public/base.html`.
El layout carga `platform.css`, `home.css`, `corporate.css` y `platform.js`.
Los wrappers `partials/nav.html` y `partials/footer.html` reutilizan los
componentes corporativos; los datos institucionales y contactos oficiales
proceden de `static/data/company.json`. Las metricas numericas proceden del
perfil CEO en base de datos, pero no se publican mientras no esten verificadas.

Los HTML de raiz, `netlify.toml`, `static/js/main.js` y
`scripts/build_corporate.py` pertenecen al despliegue estatico legacy. Se
conservan para no romper ese despliegue, pero no participan en Render y no
deben editarse para actualizar el HOME Flask. No se genero otro HOME en esta
correccion. Las fuentes legales aprobadas permanecen en `templates/public/legal/`.

El build de Render instala `requirements.txt`; el arranque declarado en
`render.yaml` y `Procfile` es `flask db upgrade && gunicorn app:app`.
Conservar PostgreSQL, `AUTO_CREATE_DB=0`, contrasena administrativa segura,
secretos en variables de entorno y disco persistente privado. El comando real
configurado en el panel de un servicio existente debe contrastarse con el
archivo del repositorio antes de publicar; editar el YAML no modifica el panel.

Las paginas `/nosotros`, `/contacto`, `/politica-de-calidad`,
`/privacy-policy`, `/terms-and-conditions` y `/preguntas-frecuentes` son publicas.
El frontend local no cambia la web desplegada hasta revisar y publicar el commit.

## Migraciones de base de datos

El proyecto usa `db.create_all()` solo para desarrollo (`FLASK_DEBUG=1` o `AUTO_CREATE_DB=1`). En staging y produccion debe usarse:

```powershell
flask db upgrade
```

Procedimiento seguro:

1. Hacer backup de la base.
2. Configurar `DATABASE_URL` hacia PostgreSQL.
3. Ejecutar `flask db upgrade` en staging.
4. Validar login, descargas, solicitudes, documentos, firmas, PDF y correo.
5. Repetir en produccion solo despues de validar staging.

## Pruebas

```powershell
python -m compileall app.py models.py tests migrations
python -m unittest discover -s tests -v
```

Las pruebas usan `sqlite:///:memory:` y almacenamiento temporal aislado. Cubren rutas publicas/admin, CSRF, contacto, descargas, manuales, solicitud de servicio, PDF, OTP, expiracion, reutilizacion de tokens, firma cliente, firma AFCyber, almacenamiento privado, correo con reintentos, compilacion DDL de PostgreSQL y permisos administrativos.

## Reglas de publicacion

La validación del candidato actual está en
`docs/VALIDACION-PREPUBLICACION-2026-10-11.md`, con versiones y resultados
estructurados. Las 37 pruebas completas pasan, pero la auditoría de
dependencias reporta un hallazgo en Werkzeug 3.1.8 y siguen pendientes las
comprobaciones reales de Render. El procedimiento de copia con backup y sin
borrar imágenes originales está en `docs/MIGRACION-IMAGENES-PERSISTENTES.md`.
No interpretar los informes históricos como confirmación del estado remoto.

No publicar si:

- `git ls-files "*.db"` devuelve resultados.
- Falta `DATABASE_URL` PostgreSQL.
- Falta SMTP real.
- Falta `PRIVATE_STORAGE_ROOT` persistente fuera del repo.
- `pip-audit` no concluye sin hallazgos criticos.
- Las pruebas no pasan.
- Hay documentos, firmas, instaladores, PDFs, bases, secretos o archivos personales preparados para commit.


## Asistente virtual y cotizaciones (12 de octubre de 2026)

El widget funciona con reglas, búsqueda y conocimiento público compartido, sin
OpenAI API ni servicios de IA de pago. Los productos se mantienen en
`static/data/products.json`; los datos corporativos en `static/data/company.json`;
servicios/FAQ/programas usan los registros públicos existentes del panel.

`/cotizacion` guarda solicitudes numeradas antes de intentar SMTP; el formulario
anterior `/contact` mantiene compatibilidad y sus mensajes administrativos.
El panel protegido `/admin/cotizaciones` permite consultar, cambiar estado y
reintentar correo. La cola persiste en PostgreSQL y no usa archivos temporales.

Está pendiente aplicar, SOLO con autorización, la migración
`20261012_0002` después de `20260722_0001`. SMTP reutiliza las variables
MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD y
MAIL_DEFAULT_SENDER. Los reintentos seguros se pueden procesar en un entorno
migrado con `flask --app app cotizaciones-reintentar --limit 20`.

Detalle de funciones, riesgos, archivos, pruebas, configuración y publicación:
`docs/ASISTENTE-COTIZACIONES.md`. Esta nueva fase tiene 52 pruebas aprobadas y
Werkzeug 3.1.9; su pip-audit no encontró vulnerabilidades conocidas. Los informes
anteriores de Werkzeug 3.1.8 son historial. Render/PostgreSQL/SMTP reales y
persistencia tras redespliegue todavía requieren validación independiente.
