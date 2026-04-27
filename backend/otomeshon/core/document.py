from __future__ import annotations

import hashlib
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from otomeshon.core.cells import (
    AnyCell,
    CellRole,
    DocumentStatus,
    ExceptionCell,
    ResultCell,
    ValidationStatus,
)


class RunSummary(BaseModel):
    run_id:          str
    started_at:      datetime
    completed_at:    datetime | None = None
    status:          DocumentStatus
    executed_by:     str
    cell_count:      int
    breach_count:    int = 0
    exception_count: int = 0


class ProcedureDocument(BaseModel):
    """
    The top-level container. Mirrors .ipynb at the document level.
    Serialises to JSON with cells stored in order.
    The otomeshon.nav namespace on each cell carries all domain metadata.
    """
    # Document identity
    doc_id:            UUID = Field(default_factory=uuid4)
    procedure_name:    str
    procedure_version: str
    policy_ref:        str | None = None

    # Scope — what this run covers
    fund_id:        str
    fund_name:      str | None = None
    valuation_date: str
    custodian:      str

    # Status
    document_status: DocumentStatus = DocumentStatus.DRAFT

    # Cells — ordered list, all types via discriminated union
    cells: list[AnyCell] = Field(default_factory=list)

    # Run history — appended each time Prefect executes this document
    run_history: list[RunSummary] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"arbitrary_types_allowed": True}

    # ── Cell access helpers ──────────────────────────────────────────────

    def cells_by_role(self, role: CellRole) -> list[AnyCell]:
        return [c for c in self.cells if c.cell_role == role]

    def cell_by_step(self, step_id: str, role: CellRole) -> AnyCell | None:
        return next(
            (c for c in self.cells
             if c.step_id == step_id and c.cell_role == role),
            None,
        )

    def append_cell(self, cell: AnyCell) -> None:
        cell.position = len(self.cells)
        self.cells.append(cell)
        self.updated_at = datetime.utcnow()

    def has_unresolved_exceptions(self) -> bool:
        return any(
            isinstance(c, ExceptionCell) and not c.is_resolved
            for c in self.cells
        )

    def is_ready_for_signoff(self) -> bool:
        return (
            not self.has_unresolved_exceptions()
            and all(
                isinstance(c, ResultCell)
                and c.nav.status in (ValidationStatus.PASS, ValidationStatus.WARN)
                for c in self.cells_by_role(CellRole.RESULT)
            )
        )

    # ── Serialisation ────────────────────────────────────────────────────

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, raw: str) -> ProcedureDocument:
        return cls.model_validate_json(raw)

    def document_hash(self) -> str:
        """Used by SignoffCell.sign() to produce the attestation hash."""
        return hashlib.sha256(self.to_json().encode()).hexdigest()
