"""Alembic: break control-loop assignee + audit events (P3)."""

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "oversight_breaks",
        sa.Column("assignee", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "oversight_breaks",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE oversight_breaks SET updated_at = NOW() WHERE updated_at IS NULL"
    )
    op.alter_column("oversight_breaks", "updated_at", nullable=False)

    op.create_table(
        "oversight_break_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "break_id",
            sa.String(length=64),
            sa.ForeignKey("oversight_breaks.break_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(length=64), nullable=False),
        sa.Column("to_status", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=256), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("assignee", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_oversight_break_events_break_id", "oversight_break_events", ["break_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_oversight_break_events_break_id", table_name="oversight_break_events"
    )
    op.drop_table("oversight_break_events")
    op.drop_column("oversight_breaks", "updated_at")
    op.drop_column("oversight_breaks", "assignee")
