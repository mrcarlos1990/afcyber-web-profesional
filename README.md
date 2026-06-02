# AFCyber SOLUTIONS Web Premium

Plataforma corporativa Flask para AFCyber SOLUTIONS con sitio publico premium, base de datos SQLite, subida de imagenes/PDF y panel administrativo protegido.

## Instalacion local

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abre `http://127.0.0.1:5000`.

## Panel administrativo

Ruta:

```text
/admin/login
```

Usuario inicial:

```text
admin@afcybersolutions.com.do
```

Contrasena inicial:

```text
Admin12345!
```

Importante: cambia esta contrasena al entrar por primera vez desde `Usuarios admin`.

## Variables de entorno

Crea un archivo `.env` opcional:

```env
SECRET_KEY=pon-una-clave-larga-y-segura
ADMIN_EMAIL=admin@afcybersolutions.com.do
ADMIN_PASSWORD=Admin12345!
FLASK_DEBUG=1
```

En produccion usa siempre un `SECRET_KEY` fuerte y cambia `ADMIN_PASSWORD`.

## Que se crea automaticamente

Al ejecutar `python app.py`, Flask crea:

- `instance/afcyber.db`
- Usuario admin inicial
- Configuracion general
- Hero principal
- Seccion Nosotros
- Seccion CEO & Founder
- Habilidades del CEO
- Certificaciones del CEO
- Servicios sugeridos
- Planes iniciales
- Portafolio demo
- Testimonios demo
- FAQ inicial
- Redes sociales iniciales

## Editar contenido

Desde el panel admin puedes editar:

- Configuracion general, identidad, logo, favicon, colores y SEO
- Hero principal
- Nosotros
- CEO & Founder, foto, descripcion, CV PDF, experiencia y estadisticas
- Habilidades del CEO
- Certificaciones del CEO
- Servicios
- Planes y precios
- Portafolio
- Testimonios
- Preguntas frecuentes
- Mensajes recibidos
- Redes sociales
- Usuarios admin

## Subidas permitidas

Imagenes permitidas:

```text
jpg, jpeg, png, webp, svg
```

CV permitido:

```text
pdf
```

Los archivos se guardan en `static/uploads/` usando `secure_filename`.

## Estructura principal

```text
app.py
models.py
extensions.py
requirements.txt
Procfile
render.yaml
README.md
templates/
  public/
  admin/
  partials/
static/
  css/
  js/
  img/
  uploads/
instance/
```

## Modelos incluidos

- User
- SiteSettings
- HeroSection
- AboutSection
- Service
- Plan
- PortfolioProject
- Testimonial
- FAQ
- ContactMessage
- SocialLink
- CEOProfile
- Skill
- Certificate

## Subir a GitHub

```bash
git init
git add .
git commit -m "Plataforma Flask AFCyber SOLUTIONS"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/afcybersolutions-web.git
git push -u origin main
```

## Desplegar en Render

1. Sube el proyecto a GitHub.
2. En Render, crea un nuevo `Web Service`.
3. Conecta el repositorio.
4. Usa:

```text
Build command: pip install -r requirements.txt
Start command: gunicorn app:app
```

Tambien puedes usar el archivo `render.yaml` como blueprint.

Configura estas variables en Render:

```text
SECRET_KEY
ADMIN_EMAIL
ADMIN_PASSWORD
FLASK_DEBUG=0
```

## Configurar dominio

1. En Render abre `Settings > Custom Domains`.
2. Agrega tu dominio, por ejemplo `afcybersolutions.com.do`.
3. Copia los registros DNS que Render indique.
4. Configuralos en tu proveedor de dominio.
5. Espera la propagacion y activa HTTPS desde Render.

## Notas de produccion

SQLite funciona bien para un sitio corporativo pequeno. Para mayor escala o persistencia administrada en Render, conviene migrar a PostgreSQL.

La apariencia conserva la linea visual original: fondo oscuro, azul neon, glassmorphism, tarjetas modernas, animaciones suaves, navbar fija y boton flotante de WhatsApp.
