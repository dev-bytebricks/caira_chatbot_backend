"""stripe plan type updated

Revision ID: 2fbb48c337bc
Revises: 072f27b5090d
Create Date: 2024-05-16 21:55:18.017976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '2fbb48c337bc'
down_revision: Union[str, None] = '072f27b5090d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'plan',
               existing_type=mysql.VARCHAR(length=200),
               type_=sa.Enum('free', 'one_month', 'three_month', 'six_month', name='plan'),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'plan',
               existing_type=sa.Enum('free', 'one_month', 'three_month', 'six_month', name='plan'),
               type_=mysql.VARCHAR(length=200),
               existing_nullable=True)
    # ### end Alembic commands ###
