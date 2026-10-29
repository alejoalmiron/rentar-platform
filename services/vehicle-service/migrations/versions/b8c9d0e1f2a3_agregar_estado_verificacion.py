from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b8c9d0e1f2a3'
down_revision = 'a7c4b1d80e21' 
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('vehiculos', sa.Column('estado_verificacion', sa.String(50), server_default='PENDIENTE', nullable=False))

def downgrade():
    op.drop_column('vehiculos', 'estado_verificacion')