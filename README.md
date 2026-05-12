# AFCyber SOLUTIONS Web Premium

Página web corporativa estática para AFCyber SOLUTIONS, lista para GitHub, Netlify y dominio personalizado.

No usa backend, Python, Flask, PHP, SQLite ni Node.js. Funciona abriendo `index.html` directamente.

## Estructura

```text
afcybersolutions-web/
├── index.html
├── README.md
├── netlify.toml
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── main.js
    ├── img/
    └── videos/
```

## Cambiar WhatsApp

Abre `static/js/main.js` y edita:

```js
whatsappNumber: "18299198058"
```

Usa formato internacional sin signos, espacios ni guiones.

## Cambiar textos y datos

En `static/js/main.js` puedes editar:

- Nombre de la empresa
- Slogan
- Teléfono
- Correo
- Ubicación
- Redes sociales
- Enlaces de botones
- Mensajes automáticos de WhatsApp

También puedes editar directamente los textos de `index.html`.

## Cambiar colores

Abre `static/css/style.css` y modifica las variables:

```css
:root {
  --primary: #1777ff;
  --secondary: #00d4ff;
  --dark: #050b18;
  --ink: #07111f;
}
```

## Cambiar imágenes

Coloca tus imágenes en:

```text
static/img/
```

Luego cambia las rutas en `index.html`. Ejemplo:

```html
<img src="static/img/mi-imagen.webp" alt="AFCyber SOLUTIONS" loading="lazy">
```

## Subir a GitHub

1. Crea un repositorio en GitHub.
2. Sube todo el contenido de `afcybersolutions-web/`.
3. Verifica que `index.html` quede en la raíz del repositorio.

## Publicar en Netlify

1. Entra a Netlify.
2. Selecciona `Add new site`.
3. Conecta tu repositorio de GitHub.
4. Configura:

```text
Build command: vacío
Publish directory: .
```

El archivo `netlify.toml` ya incluye esa configuración.

## Conectar dominio personalizado

1. En Netlify, entra a `Domain management`.
2. Agrega tu dominio, por ejemplo `afcybersolutions.com.do`.
3. Sigue las instrucciones DNS de Netlify.
4. Activa HTTPS gratuito desde Netlify.

## Firma

Diseñada por el Ing. Amauri Feliz Valenzuela.
