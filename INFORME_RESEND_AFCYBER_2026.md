# Informe técnico: Resend y notificaciones AFCyber Solutions

Fecha de verificación: 2026-10-23

## Alcance

Se integró Resend como proveedor HTTPS seleccionable para las notificaciones de contacto, cotizaciones, soporte, confirmaciones y correos de firma. El asistente determinista de `assistant.py`, los formularios existentes, SMTP, el módulo Android, el almacenamiento privado y las páginas legales se conservaron.

No se hizo push, commit, merge, despliegue, migración sobre producción ni envío de correo real.

## Implementación

- `resend_client.py`: cliente HTTP oficial contra `https://api.resend.com/emails`, Bearer, `User-Agent`, JSON HTML/texto, Reply-To, timeout y reintentos acotados.
- `app.py`: selección exclusiva por `EMAIL_PROVIDER`; Resend y SMTP no se ejecutan como fallback automático. Se validan remitente, destinatario y encabezados. Se registran estados de aceptación y errores sin tokens.
- `models.py`: `provider`, `provider_message_id`, `idempotency_key` y `accepted_at` en `EmailDelivery`, con índice único de idempotencia.
- `quotations.py`: uso de `QUOTATION_RECIPIENT` y reutilización del registro/idempotencia en reintentos de la aplicación.
- `render.yaml`, `.env.example` y `README.md`: variables Resend y alternativa SMTP documentadas.
- Plantillas administrativas: muestran proveedor, estado e identificador de proveedor, aclarando que aceptación no significa entrega final.
- `tests/test_publication_integration.py`: pruebas simuladas de API, formularios, destinos, Reply-To, CSRF, errores y reintentos.

## Variables de Render

Requeridas para producción:

```env
EMAIL_PROVIDER=resend
RESEND_API_KEY=<configurar como secreto en Render>
RESEND_FROM_EMAIL=notificaciones@afcybersolutions.com.do
CONTACT_RECIPIENT=info@afcybersolutions.com.do
SUPPORT_RECIPIENT=soporte@afcybersolutions.com.do
QUOTATION_RECIPIENT=info@afcybersolutions.com.do
RESEND_TIMEOUT_SECONDS=10
RESEND_MAX_RETRIES=2
REQUIRE_EMAIL_DELIVERY=1
```

SMTP permanece disponible solo con `EMAIL_PROVIDER=smtp`. No se debe configurar ambos proveedores como envío simultáneo.

## Migración

Se creó `migrations/versions/20261023_0004_resend_email_delivery.py`, aditiva y no destructiva. La cadena Alembic completa se ejecutó en una SQLite temporal desde `20260722_0001` hasta `20261023_0004`; se verificaron las cuatro columnas nuevas y el índice único. No se ejecutó en producción.

## Pruebas ejecutadas

- Suite unificada: **39/39 OK**.
- `python -m compileall -q .`: **exit 0**.
- `python -m pip check`: **exit 0**, sin dependencias rotas.
- `git diff --check`: **exit 0**.
- DDL PostgreSQL: prueba existente aprobada con el dialecto PostgreSQL; no había un servidor PostgreSQL aislado disponible para conexión real.
- Migración Alembic en SQLite temporal: **OK**.
- Auditoría de secretos de alta confianza en contenido rastreado: **0 coincidencias**.
- `pip-audit`: no ejecutado porque el módulo no está instalado (`No module named pip_audit`).
- Envíos reales: **0**. Todas las pruebas HTTP de Resend y SMTP fueron simuladas.

Las pruebas cubren 400, 401, 429, 500, timeout, reintentos, idempotencia, prevención de fallback SMTP, contacto, cotización, soporte, HTML, Reply-To, CSRF, antiabuso, persistencia y asistente.

## Estado Git y archivos pendientes

Rama actual: `codex/produccion-segura-afcyber`.

HEAD: `29472425306e4f6092c117ed266b5eaca427b2db`.

No se creó commit nuevo. El árbol de trabajo contiene cambios previos de consolidación y archivos personales/recursos no rastreados, incluyendo imágenes y `INFORME_CONSOLIDACION_AFCYBER_2026.md`. No deben incluirse automáticamente en un commit de esta integración. Las bases locales continúan en `instance/` y están excluidas por `.gitignore`.

## Procedimiento de prueba real autorizada

1. Configurar en Render las variables anteriores y guardar `RESEND_API_KEY` como secreto.
2. Confirmar en Resend que el dominio y `notificaciones@afcybersolutions.com.do` están habilitados para envío.
3. Desplegar primero en staging o ventana autorizada.
4. Enviar un único formulario de prueba con un buzón controlado.
5. Confirmar en los registros que el estado sea `aceptado` y conservar el `provider_message_id`.
6. Confirmar la entrega en el buzón y en el panel de Resend; la aplicación no declara entrega solo por recibir HTTP 2xx.

## Reversión

Cambiar `EMAIL_PROVIDER=smtp` y configurar sus variables SMTP permite volver al proveedor anterior sin cambiar el código. Para retirar Resend del código, revertir únicamente los cambios de esta integración y aplicar la migración de forma controlada; no borrar columnas ni registros de `EmailDelivery` sin un procedimiento aprobado.

## Estado final

**Listo para revisión técnica y staging condicionado a configurar `RESEND_API_KEY`. No listo para producción todavía**: falta configurar y verificar el secreto en Render, ejecutar la migración en staging PostgreSQL y realizar una prueba real autorizada. No se efectuó publicación.

Referencias oficiales: [Resend Send Email API](https://resend.com/docs/api-reference/emails/send-email) y [Resend API Introduction](https://resend.com/docs/api-reference/introduction).
