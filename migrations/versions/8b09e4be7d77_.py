"""empty message

Revision ID: 8b09e4be7d77
Revises: 311c22ae41d1
Create Date: 2018-09-12 19:51:19.796000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '8b09e4be7d77'
down_revision = '311c22ae41d1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tb_msdetail', sa.Column('interval', sa.Float(), nullable=True))
    op.drop_column('tb_msdetail', 'dates')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tb_msdetail', sa.Column('dates', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.drop_column('tb_msdetail', 'interval')
    # ### end Alembic commands ###
