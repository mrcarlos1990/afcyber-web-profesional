# Migraciones Flask-Migrate/Alembic

Este directorio reemplaza la migracion SQL manual. El proyecto usa SQLAlchemy y puede migrarse con Flask-Migrate cuando la dependencia este instalada.

Procedimiento seguro:

1. Hacer backup de la base actual.
2. Configurar `DATABASE_URL` apuntando a PostgreSQL en staging.
3. Ejecutar `flask db upgrade`.
4. Validar login, descargas, solicitudes, documentos, firmas, PDF y correo.
5. Repetir el proceso en produccion solo despues de validar staging.

La primera revision es no destructiva: crea tablas faltantes a partir de los modelos y no elimina datos en `downgrade`.
