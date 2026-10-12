"""Persistent quotations, outbox and distributed public rate buckets.
Revision ID: 20261012_0002
Revises: 20260722_0001
"""
from alembic import op
from models import QuoteRequest, QuoteMail, PublicRateBucket
revision = '20261012_0002'
down_revision = '20260722_0001'
branch_labels = None
depends_on = None

def upgrade():
    # The historical baseline uses current metadata on empty databases.
    # checkfirst also makes upgrading existing baseline databases safe.
    bind=op.get_bind()
    for table in [QuoteRequest.__table__, QuoteMail.__table__, PublicRateBucket.__table__]:
        table.create(bind=bind, checkfirst=True)

def downgrade():
    raise RuntimeError('Las cotizaciones y registros de correo deben conservarse. Restauración requiere un procedimiento explícito aprobado; no se eliminan tablas automáticamente.')
