"""android app version distribution

Revision ID: 20261006_0002
Revises: 20260722_0001
Create Date: 2026-10-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20261006_0002"
down_revision = "20260722_0001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("android_app_version"):
        op.create_table(
            "android_app_version",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("app_slug", sa.String(length=80), nullable=False),
            sa.Column("version", sa.String(length=60), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("release_notes", sa.Text(), nullable=True),
            sa.Column("min_sdk", sa.Integer(), nullable=True),
            sa.Column("file_path", sa.String(length=255), nullable=False),
            sa.Column("original_name", sa.String(length=255), nullable=True),
            sa.Column("file_size", sa.Integer(), nullable=True),
            sa.Column("sha256", sa.String(length=64), nullable=False),
            sa.Column("signature_cert_sha256", sa.String(length=64), nullable=True),
            sa.Column("signature_verified", sa.Boolean(), nullable=True),
            sa.Column("is_public", sa.Boolean(), nullable=True),
            sa.Column("status", sa.String(length=40), nullable=True),
            sa.Column("published_on", sa.Date(), nullable=True),
            sa.Column("download_count", sa.Integer(), nullable=True),
            sa.Column("last_downloaded_at", sa.DateTime(), nullable=True),
            sa.Column("uploaded_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("sha256"),
            sa.UniqueConstraint("uuid"),
        )
        op.create_index("ix_android_app_public", "android_app_version", ["app_slug", "is_public"], unique=False)
    else:
        columns = {column["name"] for column in inspector.get_columns("android_app_version")}
        if "description" not in columns:
            op.add_column("android_app_version", sa.Column("description", sa.Text(), nullable=True))
    index_names = {index["name"] for index in sa.inspect(bind).get_indexes("android_app_version")}
    if "uq_android_app_public_version" not in index_names:
        op.create_index(
            "uq_android_app_public_version",
            "android_app_version",
            ["app_slug"],
            unique=True,
            postgresql_where=sa.text("is_public = true AND status = 'publicado'"),
            sqlite_where=sa.text("is_public = 1 AND status = 'publicado'"),
        )
    if not inspector.has_table("admin_audit_event"):
        op.create_table(
            "admin_audit_event",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=80), nullable=False),
            sa.Column("item_type", sa.String(length=80), nullable=False),
            sa.Column("item_id", sa.Integer(), nullable=True),
            sa.Column("detail", sa.Text(), nullable=True),
            sa.Column("ip_hash", sa.String(length=64), nullable=True),
            sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["actor_id"], ["user.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
        )
        op.create_index("ix_admin_audit_item", "admin_audit_event", ["item_type", "item_id"], unique=False)


def downgrade():
    # No se elimina el historial de APKs para evitar perdida accidental de versiones publicadas.
    pass
