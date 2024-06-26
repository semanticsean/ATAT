"""Add voice column to Agent model

Revision ID: bac681d72589
Revises: 4c04acf7b265
Create Date: 2024-04-26 08:17:04.152872

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bac681d72589'
down_revision = '4c04acf7b265'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('agent', schema=None) as batch_op:
        batch_op.add_column(sa.Column('voice', sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('agent', schema=None) as batch_op:
        batch_op.drop_column('voice')

    # ### end Alembic commands ###
