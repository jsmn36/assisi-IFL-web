"""Add task history table

Revision ID: add_task_history
Revises: add_performance_indexes
Create Date: 2024-01-23
"""
from alembic import op
import sqlalchemy as sa

revision = "add_task_history"
down_revision = "add_performance_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "task_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(255), nullable=False),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("task_args", sa.Text()),
        sa.Column("task_kwargs", sa.Text()),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("result", sa.Text()),
        sa.Column("error", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("worker_name", sa.String(255)),
        sa.Column("queue_name", sa.String(100)),
        sa.Column("retries", sa.Integer(), default=0),
        sa.Column("max_retries", sa.Integer(), default=3),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_history_task_id", "task_history", ["task_id"], unique=True)
    op.create_index("ix_task_history_task_name", "task_history", ["task_name"])
    op.create_index("ix_task_history_status", "task_history", ["status"])


def downgrade():
    op.drop_index("ix_task_history_status", table_name="task_history")
    op.drop_index("ix_task_history_task_name", table_name="task_history")
    op.drop_index("ix_task_history_task_id", table_name="task_history")
    op.drop_table("task_history")
