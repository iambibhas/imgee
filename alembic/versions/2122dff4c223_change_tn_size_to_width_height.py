"""change thumbnail size to width and height

Revision ID: 2122dff4c223
Revises: 4b2844325813
Create Date: 2013-10-18 18:15:47.189909

"""

# revision identifiers, used by Alembic.
revision = '2122dff4c223'
down_revision = '4b2844325813'

from alembic import op
import sqlalchemy as sa

import sys
sys.path.append('../../')
from sqlalchemy.sql import select, bindparam, column
from imgee.models import Thumbnail

def upgrade():
    op.add_column('thumbnail', sa.Column('width', sa.Integer(), nullable=True))
    op.add_column('thumbnail', sa.Column('height', sa.Integer(), nullable=True))
    
    connection = op.get_bind()
    tn = Thumbnail.__table__
    result = connection.execute(select([column('id'), column('size')], from_obj=tn))
    w_h = [dict(tnid=r.id, w=int(r.size.split('x')[0]), h=int(r.size.split('x')[1])) for r in result]
    updt_stmt = tn.update().where(tn.c.id == bindparam('tnid')).values(width=bindparam('w'), height=bindparam('h'))
    connection.execute(updt_stmt, w_h)


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('thumbnail', 'height')
    op.drop_column('thumbnail', 'width')
    ### end Alembic commands ###
