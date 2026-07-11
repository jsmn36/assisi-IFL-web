"""fix_rate_plan_and_stay_schema_mismatches

Revision ID: bfa2b28a46f7
Revises: 888d204ad144
Create Date: 2026-04-07 19:00:10.015239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfa2b28a46f7'
down_revision: Union[str, None] = '888d204ad144'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table("rate_plans") as batch_op:
        batch_op.alter_column("room_type_id", existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table("stays") as batch_op:
        batch_op.alter_column("property_id", existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column("guest_id", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("stays") as batch_op:
        batch_op.alter_column("guest_id", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("property_id", existing_type=sa.Integer(), nullable=False)

    with op.batch_alter_table("rate_plans") as batch_op:
        batch_op.alter_column("room_type_id", existing_type=sa.Integer(), nullable=False)
