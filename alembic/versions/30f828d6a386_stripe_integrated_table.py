"""stripe-integrated-table

Revision ID: 30f828d6a386
Revises: 894e020a1e6d
Create Date: 2024-04-14 21:27:14.659088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30f828d6a386'
down_revision: Union[str, None] = '894e020a1e6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('plan', sa.Enum('free', 'one_month', 'three_month', 'six_month', name='plan'), nullable=True))
    op.add_column('users', sa.Column('stripeId', sa.String(length=200), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'stripeId')
    op.drop_column('users', 'plan')
    # ### end Alembic commands ###
