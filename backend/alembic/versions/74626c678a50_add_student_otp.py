"""add_student_otp

Revision ID: 74626c678a50
Revises: tier3_2026_05_14
Create Date: 2026-08-05 14:31:27.744480

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74626c678a50'
down_revision: Union[str, None] = 'tier3_2026_05_14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('student_otps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=200), nullable=False),
    sa.Column('otp_code', sa.String(length=10), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_otps_email'), 'student_otps', ['email'], unique=True)
    op.create_index(op.f('ix_student_otps_id'), 'student_otps', ['id'], unique=False)
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), server_default='1', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'is_email_verified')
    op.drop_index(op.f('ix_student_otps_id'), table_name='student_otps')
    op.drop_index(op.f('ix_student_otps_email'), table_name='student_otps')
    op.drop_table('student_otps')
