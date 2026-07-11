"""merge_all_heads

Revision ID: 23763de82206
Revises: add_performance_indexes, da84a6ef3185
Create Date: 2026-03-25 14:42:09.626198

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "23763de82206"
down_revision: Union[str, None] = ("add_performance_indexes", "da84a6ef3185")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
