# AFCyber SOLUTIONS Platform

Plataforma corporativa premium para AFCyber SOLUTIONS con sitio publico tecnologico oscuro y panel administrativo completo.

## Tecnologias

- Flask
- SQLite
- Flask-SQLAlchemy
- Flask-Login
- HTML5, CSS3, JavaScript
- Bootstrap 5
- Font Awesome
- Gunicorn para Render

## Instalacion local

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crea un archivo `.env` basado en `.env.example`:

```env
SECRET_KEY=coloca-una-clave-segura
DATABASE_URL=sqlite:///instance/afcyber_platform.db
ADMIN_EMAIL=admin@afcybersolutions.com.do
ADMIN_PASSWORD=Admin12345!
FLASK_DEBUG=1
```

Ejecuta:

```bash
python app.py
```

Abre:

- Web publica: `http://127.0.0.1:5000`
- Panel admin: `http://127.0.0.1:5000/admin/login`

## Usuario inicial

- Usuario: `admin@afcybersolutions.com.do`
- Contrasena inicial: `Admin12345!`

Importante: cambia esta contrasena al entrar por primera vez desde `Usuarios admin`.

## Que se puede editar desde admin

- Configuracion general
- Logo, favicon e identidad
- Colores del sitio
- SEO y Open Graph
- Hero principal
- Nosotros
- CEO & Fundador
- Servicios
- Planes y precios
- Portafolio
- Testimonios
- Preguntas frecuentes
- Redes sociales
- Mensajes recibidos
- Usuarios administradores

## Subidas permitidas

Imagenes:

- jpg
- jpeg
- png
- webp
- svg

CV del CEO:

- pdf

Los archivos se guardan en `static/uploads`.

## Subir a GitHub

1. Crea un repositorio en GitHub.
2. Sube todos los archivos del proyecto.
3. No subas `.env`, `instance/` ni archivos privados.

## Desplegar en Render

Render puede usar el archivo `render.yaml`, o puedes configurar manualmente:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

Variables recomendadas:

```env
SECRET_KEY=clave-segura-produccion
DATABASE_URL=sqlite:///instance/afcyber_platform.db
ADMIN_EMAIL=admin@afcybersolutions.com.do
ADMIN_PASSWORD=Admin12345!
```

En produccion cambia `ADMIN_PASSWORD` antes del primer despliegue o cambia la contrasena desde el panel.

## Configurar dominio

1. Despliega el servicio en Render.
2. En Render, abre `Settings > Custom Domains`.
3. Agrega tu dominio, por ejemplo `afcybersolutions.com.do`.
4. Configura los DNS segun las instrucciones de Render.
5. Activa HTTPS.

## Editar contenido

Todo el contenido principal se administra desde `/admin`:

- Los servicios se crean en `Servicios`.
- Los planes se gestionan en `Planes`.
- Los proyectos se suben en `Portafolio`.
- El perfil del fundador se edita en `CEO/Fundador`.
- Los mensajes del formulario se ven en `Mensajes`.

La web crea automaticamente la base de datos, configuracion inicial, contenido sugerido y usuario admin inicial al ejecutar `python app.py`.
Actualización realizada el 12/05/2026.
