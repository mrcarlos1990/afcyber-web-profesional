"""Add durable quotations, mail jobs and public rate buckets.

This revision is additive and follows the existing Resend delivery revision.
No existing table, column or record is removed.
"""

from alembic import op
import sqlalchemy as sa


revision = "20261025_0003"
down_revision = "20261025_0002"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("quote_request"):
        op.create_table(
            "quote_request",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("submission_key", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("company", sa.String(length=160)),
            sa.Column("phone", sa.String(length=60), nullable=False),
            sa.Column("email", sa.String(length=160)),
            sa.Column("requested_service", sa.String(length=160), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("budget", sa.String(length=120)),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="RECIBIDA"),
            sa.Column("consent_version", sa.String(length=40), nullable=False, server_default="2026-10"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("submission_key", name="uq_quote_request_submission_key"),
        )

    inspector = sa.inspect(bind)
    if not inspector.has_table("quote_mail"):
        op.create_table(
            "quote_mail",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("quote_id", sa.Integer(), nullable=False),
            sa.Column("kind", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDIENTE"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("delivery_id", sa.Integer()),
            sa.ForeignKeyConstraint(["quote_id"], ["quote_request.id"]),
            sa.ForeignKeyConstraint(["delivery_id"], ["email_delivery.id"]),
            sa.UniqueConstraint("quote_id", "kind", name="uq_quote_mail_kind"),
        )

    inspector = sa.inspect(bind)
    if not inspector.has_table("public_rate_bucket"):
        op.create_table(
            "public_rate_bucket",
            sa.Column("key", sa.String(length=64), primary_key=True),
            sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("expires_at", sa.Integer(), nullable=False),
        )
        op.create_index("ix_public_rate_bucket_expires_at", "public_rate_bucket", ["expires_at"])


def downgrade():
    raise RuntimeError(
        "Las cotizaciones y registros de correo deben conservarse. "
        "La reversión requiere un procedimiento explícito aprobado."
    )
