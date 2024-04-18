"""test_table

Revision ID: a1210215dc3f
Revises: 607ce6d68dd1
Create Date: 2024-04-17 15:30:28.986774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1210215dc3f'
down_revision: Union[str, None] = '607ce6d68dd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('admin_config', sa.Column('llm_streaming', sa.Boolean(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('admin_config', 'llm_streaming')
    # ### end Alembic commands ###
