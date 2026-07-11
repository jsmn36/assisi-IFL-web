"""merge_task_history_head

Revision ID: 78b5264b19e3
Revises: add_task_history, a5fa3706c1a1
Create Date: 2026-03-28 11:15:44.587054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "78b5264b19e3"
down_revision: Union[str, None] = ("add_task_history", "a5fa3706c1a1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
