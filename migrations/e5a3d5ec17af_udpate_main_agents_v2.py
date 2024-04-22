"""udpate main agents v2

Revision ID: e5a3d5ec17af
Revises: 129e7ee95935
Create Date: 2024-04-22 16:39:35.275585

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e5a3d5ec17af'
down_revision = '129e7ee95935'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('main_agent',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('data', sa.Text(), nullable=False),
    sa.Column('image_data', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('agents_data')
        batch_op.drop_column('images_data')
        batch_op.drop_column('thumbnail_images_data')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('thumbnail_images_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('images_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('agents_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))

    op.drop_table('main_agent')
    # ### end Alembic commands ###