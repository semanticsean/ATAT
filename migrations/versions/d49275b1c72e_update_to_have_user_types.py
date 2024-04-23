"""update to have user types

Revision ID: d49275b1c72e
Revises: 4744431df6a0
Create Date: 2024-04-23 05:25:28.334720

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd49275b1c72e'
down_revision = '4744431df6a0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('agent', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agent_type', sa.String(length=20), nullable=True))

    with op.batch_alter_table('timeframe', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agent_type', sa.String(length=20), nullable=True))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agent_type', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('agent_type')

    with op.batch_alter_table('timeframe', schema=None) as batch_op:
        batch_op.drop_column('agent_type')

    with op.batch_alter_table('agent', schema=None) as batch_op:
        batch_op.drop_column('agent_type')

    # ### end Alembic commands ###
