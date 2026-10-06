"""SQLAlchemy models for durable custodian oversight control objects."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.trade import Base


class OversightRunRow(Base):
    """One reconciliation run (fixture or ingest). Moat control object root."""

    __tablename__ = "oversight_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ran_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="fixture")
    rule_family: Mapped[str] = mapped_column(String(256), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), nullable=False)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    positions: Mapped[list["OversightPositionRow"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    comparisons: Mapped[list["OversightComparisonRow"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    rule_results: Mapped[list["OversightRuleResultRow"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    breaks: Mapped[list["OversightBreakRow"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class OversightPositionRow(Base):
    __tablename__ = "oversight_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("oversight_runs.run_id", ondelete="CASCADE"), index=True
    )
    contract_id: Mapped[str] = mapped_column(String(256), nullable=False)
    book: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    security_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    contract_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    run: Mapped[OversightRunRow] = relationship(back_populates="positions")


class OversightComparisonRow(Base):
    __tablename__ = "oversight_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("oversight_runs.run_id", ondelete="CASCADE"), index=True
    )
    account_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    security_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    break_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    comparison_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    run: Mapped[OversightRunRow] = relationship(back_populates="comparisons")


class OversightRuleResultRow(Base):
    __tablename__ = "oversight_rule_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("oversight_runs.run_id", ondelete="CASCADE"), index=True
    )
    rule_result_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rule_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contract_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    run: Mapped[OversightRunRow] = relationship(back_populates="rule_results")


class OversightBreakRow(Base):
    __tablename__ = "oversight_breaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("oversight_runs.run_id", ondelete="CASCADE"), index=True
    )
    break_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    reason_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="open")
    severity: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assignee: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    contract_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    run: Mapped[OversightRunRow] = relationship(back_populates="breaks")
    events: Mapped[list["OversightBreakEventRow"]] = relationship(
        back_populates="break_row", cascade="all, delete-orphan"
    )


class OversightBreakEventRow(Base):
    """Immutable audit events for break control-loop transitions."""

    __tablename__ = "oversight_break_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    break_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("oversight_breaks.break_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str] = mapped_column(String(64), nullable=False)
    to_status: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(256), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assignee: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    break_row: Mapped[OversightBreakRow] = relationship(back_populates="events")
