"""merge_search_head

Revision ID: a5fa3706c1a1
Revises: add_search, 23763de82206
Create Date: 2026-03-26 18:08:04.977456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a5fa3706c1a1"
down_revision: Union[str, None] = ("add_search", "23763de82206")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
