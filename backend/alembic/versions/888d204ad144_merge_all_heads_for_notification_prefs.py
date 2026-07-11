"""merge_all_heads_for_notification_prefs

Revision ID: 888d204ad144
Revises: add_notification_preferences, 78b5264b19e3
Create Date: 2026-03-28 11:25:30.173394

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "888d204ad144"
down_revision: Union[str, None] = ("add_notification_preferences", "78b5264b19e3")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
