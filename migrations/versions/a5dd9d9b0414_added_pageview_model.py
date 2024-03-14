"""Added PageView model

Revision ID: a5dd9d9b0414
Revises: 7f3e9c2445bc
Create Date: 2024-03-14 12:15:33.785851

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5dd9d9b0414'
down_revision = '7f3e9c2445bc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('page_view',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('page', sa.String(length=50), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('page_view')
    # ### end Alembic commands ###