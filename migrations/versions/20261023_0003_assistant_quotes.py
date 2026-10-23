"""Add persistent quotation, mail outbox and public rate-limit tables.

This migration is additive and follows the Android distribution migration. It
does not alter historical revisions or delete existing business data.
"""

from alembic import op

from models import PublicRateBucket, QuoteMail, QuoteRequest


revision = "20261023_0003"
down_revision = "20261006_0002"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    for table in (QuoteRequest.__table__, QuoteMail.__table__, PublicRateBucket.__table__):
        table.create(bind=bind, checkfirst=True)


def downgrade():
    raise RuntimeError(
        "Las cotizaciones y registros de correo deben conservarse. "
        "La restauración requiere un procedimiento explícito aprobado; "
        "no se eliminan tablas automáticamente."
    )
