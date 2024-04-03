"""increased llm prompt length

Revision ID: 607ce6d68dd1
Revises: d4c9e7f6f9b3
Create Date: 2024-04-03 16:41:32.683429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '607ce6d68dd1'
down_revision: Union[str, None] = 'd4c9e7f6f9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('admin_config', 'llm_prompt',
               existing_type=mysql.VARCHAR(length=250),
               type_=sa.Text(),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('admin_config', 'llm_prompt',
               existing_type=sa.Text(),
               type_=mysql.VARCHAR(length=250),
               existing_nullable=False)
    # ### end Alembic commands ###
