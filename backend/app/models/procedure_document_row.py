"""SQLAlchemy persistence for NAV procedure documents (JSON document blob)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.trade import Base


class ProcedureDocumentRow(Base):
    """One row per procedure document; full payload stored as JSON for API round-trip."""

    __tablename__ = "procedure_documents"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
