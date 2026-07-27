"""Alembic migration: durable oversight control objects (P1a)."""

from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "oversight_runs",
        sa.Column("run_id", sa.String(length=64), primary_key=True),
        sa.Column("ran_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="fixture"),
        sa.Column("rule_family", sa.String(length=256), nullable=False),
        sa.Column("rule_version", sa.String(length=32), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_oversight_runs_ran_at", "oversight_runs", ["ran_at"])

    op.create_table(
        "oversight_positions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.String(length=64),
            sa.ForeignKey("oversight_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("contract_id", sa.String(length=256), nullable=False),
        sa.Column("book", sa.String(length=64), nullable=True),
        sa.Column("account_id", sa.String(length=128), nullable=True),
        sa.Column("security_id", sa.String(length=128), nullable=True),
        sa.Column("contract_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_oversight_positions_run_id", "oversight_positions", ["run_id"])

    op.create_table(
        "oversight_comparisons",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.String(length=64),
            sa.ForeignKey("oversight_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("account_id", sa.String(length=128), nullable=True),
        sa.Column("security_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("break_id", sa.String(length=64), nullable=True),
        sa.Column("comparison_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_oversight_comparisons_run_id", "oversight_comparisons", ["run_id"])

    op.create_table(
        "oversight_rule_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.String(length=64),
            sa.ForeignKey("oversight_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rule_result_id", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=256), nullable=True),
        sa.Column("triggered", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("contract_json", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_oversight_rule_results_run_id", "oversight_rule_results", ["run_id"]
    )
    op.create_index(
        "ix_oversight_rule_results_rule_result_id",
        "oversight_rule_results",
        ["rule_result_id"],
    )

    op.create_table(
        "oversight_breaks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.String(length=64),
            sa.ForeignKey("oversight_runs.run_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("break_id", sa.String(length=64), nullable=False),
        sa.Column("account_id", sa.String(length=128), nullable=True),
        sa.Column("reason_code", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="open"),
        sa.Column("severity", sa.String(length=64), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("contract_json", sa.JSON(), nullable=False),
        sa.UniqueConstraint("break_id", name="uq_oversight_breaks_break_id"),
    )
    op.create_index("ix_oversight_breaks_run_id", "oversight_breaks", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_oversight_breaks_run_id", table_name="oversight_breaks")
    op.drop_table("oversight_breaks")
    op.drop_index(
        "ix_oversight_rule_results_rule_result_id", table_name="oversight_rule_results"
    )
    op.drop_index("ix_oversight_rule_results_run_id", table_name="oversight_rule_results")
    op.drop_table("oversight_rule_results")
    op.drop_index("ix_oversight_comparisons_run_id", table_name="oversight_comparisons")
    op.drop_table("oversight_comparisons")
    op.drop_index("ix_oversight_positions_run_id", table_name="oversight_positions")
    op.drop_table("oversight_positions")
    op.drop_index("ix_oversight_runs_ran_at", table_name="oversight_runs")
    op.drop_table("oversight_runs")
