"""merge heads

Revision ID: da84a6ef3185
Revises: add_advanced_features, add_notifications
Create Date: 2026-03-17 21:32:11.887439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "da84a6ef3185"
down_revision: Union[str, None] = ("add_advanced_features", "add_notifications")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
