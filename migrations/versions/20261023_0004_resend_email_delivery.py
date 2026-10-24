"""Record provider and idempotency metadata for email deliveries.

This revision is additive. Existing delivery rows remain intact and receive
the historical SMTP provider as their database default.
"""

from alembic import op
import sqlalchemy as sa


revision = "20261023_0004"
down_revision = "20261023_0003"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("email_delivery"):
        return

    columns = {column["name"] for column in inspector.get_columns("email_delivery")}
    if "provider" not in columns:
        op.add_column(
            "email_delivery",
            sa.Column("provider", sa.String(length=30), nullable=False, server_default="smtp"),
        )
    if "provider_message_id" not in columns:
        op.add_column("email_delivery", sa.Column("provider_message_id", sa.String(length=255), nullable=True))
    if "idempotency_key" not in columns:
        op.add_column("email_delivery", sa.Column("idempotency_key", sa.String(length=255), nullable=True))
    if "accepted_at" not in columns:
        op.add_column("email_delivery", sa.Column("accepted_at", sa.DateTime(), nullable=True))

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("email_delivery")}
    if "uq_email_delivery_idempotency_key" not in indexes:
        op.create_index("uq_email_delivery_idempotency_key", "email_delivery", ["idempotency_key"], unique=True)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("email_delivery"):
        return
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("email_delivery")}
    if "uq_email_delivery_idempotency_key" in indexes:
        op.drop_index("uq_email_delivery_idempotency_key", table_name="email_delivery")
    columns = {column["name"] for column in sa.inspect(bind).get_columns("email_delivery")}
    for name in ("accepted_at", "idempotency_key", "provider_message_id", "provider"):
        if name in columns:
            with op.batch_alter_table("email_delivery") as batch_op:
                batch_op.drop_column(name)
