"""production prep baseline

Revision ID: 20260722_0001
Revises:
Create Date: 2026-07-22
"""

from alembic import op
import sqlalchemy as sa

from extensions import db
import models  # noqa: F401


revision = "20260722_0001"
down_revision = None
branch_labels = None
depends_on = None


def _has_column(inspector, table_name, column_name):
    if not inspector.has_table(table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade():
    bind = op.get_bind()
    db.metadata.create_all(bind=bind, checkfirst=True)
    inspector = sa.inspect(bind)
    if inspector.has_table("signature_request") and not _has_column(inspector, "signature_request", "version_number"):
        op.add_column("signature_request", sa.Column("version_number", sa.Integer(), nullable=True, server_default="1"))
    if inspector.has_table("electronic_signature") and not _has_column(inspector, "electronic_signature", "version_number"):
        op.add_column("electronic_signature", sa.Column("version_number", sa.Integer(), nullable=True, server_default="1"))


def downgrade():
    # No se eliminan tablas ni columnas para evitar perdida accidental de documentos, firmas o auditoria.
    pass
