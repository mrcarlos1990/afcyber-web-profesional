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
SECRET_KEY=clave-aleatoria-de-32-caracteres-o-mas
SIGNING_SECRET=otra-clave-aleatoria-para-tokens-y-hashes
DATABASE_URL=postgresql://...
ADMIN_EMAIL=admin@afcybersolutions.com.do
ADMIN_PASSWORD=contrasena-inicial-fuerte
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

No publicar si:

- `git ls-files "*.db"` devuelve resultados.
- Falta `DATABASE_URL` PostgreSQL.
- Falta SMTP real.
- Falta `PRIVATE_STORAGE_ROOT` persistente fuera del repo.
- `pip-audit` no concluye sin hallazgos criticos.
- Las pruebas no pasan.
- Hay documentos, firmas, instaladores, PDFs, bases, secretos o archivos personales preparados para commit.
