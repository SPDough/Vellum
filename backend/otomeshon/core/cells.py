from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field, model_validator


# ── Enumerations ──────────────────────────────────────────────────────────────

class CellRole(str, Enum):
    NARRATIVE  = "narrative"
    REASONING  = "reasoning"
    VALIDATION = "validation"
    RESULT     = "result"
    EXCEPTION  = "exception"
    SIGNOFF    = "signoff"


class ExecutionMode(str, Enum):
    AUTONOMOUS  = "autonomous"
    SUPERVISED  = "supervised"
    GATED       = "gated"


class ValidationStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    PASS      = "pass"
    WARN      = "warn"
    FAIL      = "fail"
    BREACH    = "breach"
    SKIPPED   = "skipped"


class DocumentStatus(str, Enum):
    DRAFT     = "draft"
    IN_REVIEW = "in_review"
    APPROVED  = "approved"
    LOCKED    = "locked"


class BreachType(str, Enum):
    TOLERANCE_EXCEEDED  = "tolerance_exceeded"
    DATA_MISSING        = "data_missing"
    DATA_STALE          = "data_stale"
    RECONCILIATION_FAIL = "reconciliation_fail"
    ANOMALY_DETECTED    = "anomaly_detected"


class HumanDecision(str, Enum):
    ACCEPT_WITH_NOTE = "accept_with_note"
    ESCALATE         = "escalate"
    RESTATE          = "restate"
    OVERRIDE         = "override"
    DEFER            = "defer"


# ── Provenance ────────────────────────────────────────────────────────────────

class ToolCallRecord(BaseModel):
    """Immutable record of a single MCP tool invocation."""
    tool_name:   str
    mcp_server:  str
    params:      dict[str, Any]
    result_hash: str
    duration_ms: int
    called_at:   datetime = Field(default_factory=datetime.utcnow)
    success:     bool


class ProvenanceChain(BaseModel):
    """
    Full audit trace for any AI-generated cell content.
    Stored in ReasoningCell and ValidationCell nav metadata.
    """
    prompt_hash:   str
    model_id:      str
    agent_id:      str
    agent_version: str
    temperature:   float = 0.1
    token_count:   int
    tool_calls:    list[ToolCallRecord] = Field(default_factory=list)
    data_hash:     str
    captured_at:   datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def compute_prompt_hash(cls, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()

    @classmethod
    def compute_data_hash(cls, data: Any) -> str:
        serialised = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialised.encode()).hexdigest()


# ── Remediation ───────────────────────────────────────────────────────────────

class RemediationOption(BaseModel):
    """One AI-proposed resolution path for an exception."""
    option:      HumanDecision
    label:       str
    description: str
    risk_level:  Literal["low", "medium", "high"] = "medium"


# ── Per-cell OtomeshonNav namespace models ────────────────────────────────────

class BaseNav(BaseModel):
    """Fields common to every nav model."""
    step:       str
    step_label: str
    policy_ref: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NarrativeNav(BaseNav):
    step_owner:     str
    regulatory_ref: str | None = None
    immutable:      bool = False


class ReasoningNav(BaseNav):
    chain_of_thought:        str
    confidence_score:        float
    provenance:              ProvenanceChain
    auto_escalate_threshold: float = 0.7


class ValidationNav(BaseNav):
    mcp_tool:       str
    mcp_server:     str
    mcp_params:     dict[str, Any]
    tolerance_abs:  float | None = None
    tolerance_bps:  float | None = None
    execution_mode: ExecutionMode = ExecutionMode.SUPERVISED
    agent_id:       str | None = None
    provenance:     ProvenanceChain | None = None


class ResultNav(BaseNav):
    status:          ValidationStatus
    run_id:          str
    result_delta:    float | None = None
    result_value:    float | None = None
    expected_value:  float | None = None
    data_hash:       str
    anomaly_flags:   list[str] = Field(default_factory=list)
    agent_narrative: str | None = None
    executed_at:     datetime = Field(default_factory=datetime.utcnow)


class ExceptionNav(BaseNav):
    breach_type:              BreachType
    breach_magnitude:         str
    triggering_run_id:        str
    agent_diagnosis:          str
    confidence_in_diagnosis:  float
    prior_occurrence_run_ids: list[str] = Field(default_factory=list)
    remediation_options:      list[RemediationOption] = Field(default_factory=list)
    escalation_path:          list[str] = Field(default_factory=list)
    human_decision:           HumanDecision | None = None
    decision_rationale:       str | None = None
    decision_by:              str | None = None
    decision_at:              datetime | None = None


class SignoffNav(BaseNav):
    reviewer:        str
    reviewer_role:   str
    approved_at:     datetime | None = None
    document_hash:   str | None = None
    override_reason: str | None = None


# ── Abstract BaseCell ─────────────────────────────────────────────────────────

class BaseCell(BaseModel):
    """
    Abstract base for all Vellum procedure document cells.
    Do not instantiate directly — use a concrete subclass.
    The `cell_role` field is the discriminator for the AnyCell union.
    """
    cell_id:  UUID = Field(default_factory=uuid4)
    position: int
    step_id:  str
    source:   str = ""
    outputs:  list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    cell_role: CellRole

    model_config = {"arbitrary_types_allowed": True}

    def serialise_nav(self, nav: BaseNav) -> None:
        """Write the nav model into metadata["otomeshon.nav"]."""
        self.metadata["otomeshon.nav"] = nav.model_dump(mode="json")

    def get_nav_raw(self) -> dict[str, Any] | None:
        return self.metadata.get("otomeshon.nav")

    @computed_field
    @property
    def cell_hash(self) -> str:
        """SHA-256 of the cell's source + nav metadata. Detects tampering."""
        payload = json.dumps(
            {"source": self.source, "nav": self.get_nav_raw()},
            sort_keys=True, default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()


# ── Concrete cell types ───────────────────────────────────────────────────────

class NarrativeCell(BaseCell):
    """
    Human-authored procedure text. Immutable once document is APPROVED.
    Cole reads this as context before generating a ReasoningCell.
    """
    cell_role: Literal[CellRole.NARRATIVE] = CellRole.NARRATIVE
    nav:       NarrativeNav

    @model_validator(mode="after")
    def sync_nav_to_metadata(self) -> NarrativeCell:
        self.serialise_nav(self.nav)
        return self


class ReasoningCell(BaseCell):
    """
    AI-generated chain-of-thought. No executable source.
    If confidence_score < auto_escalate_threshold, the downstream
    ValidationCell's execution_mode is automatically promoted to GATED.
    """
    cell_role: Literal[CellRole.REASONING] = CellRole.REASONING
    nav:       ReasoningNav

    @model_validator(mode="after")
    def sync_nav_to_metadata(self) -> ReasoningCell:
        self.serialise_nav(self.nav)
        return self

    @property
    def should_escalate(self) -> bool:
        return self.nav.confidence_score < self.nav.auto_escalate_threshold


class ValidationCell(BaseCell):
    """
    Agent-executed MCP tool invocation. Execution mode governs
    whether a human gate is required before or after execution.
    """
    cell_role: Literal[CellRole.VALIDATION] = CellRole.VALIDATION
    nav:       ValidationNav

    @model_validator(mode="after")
    def sync_nav_to_metadata(self) -> ValidationCell:
        self.serialise_nav(self.nav)
        return self

    @property
    def requires_human_approval_before(self) -> bool:
        return self.nav.execution_mode == ExecutionMode.GATED

    @property
    def requires_human_review_after(self) -> bool:
        return self.nav.execution_mode in (
            ExecutionMode.SUPERVISED, ExecutionMode.GATED
        )


class ResultCell(BaseCell):
    """
    System-written after ValidationCell executes. Never written by a human.
    If status is BREACH, Randy fires an ExceptionCell.
    """
    cell_role: Literal[CellRole.RESULT] = CellRole.RESULT
    nav:       ResultNav

    @model_validator(mode="after")
    def sync_nav_to_metadata(self) -> ResultCell:
        self.serialise_nav(self.nav)
        return self

    @property
    def is_breach(self) -> bool:
        return self.nav.status == ValidationStatus.BREACH

    @property
    def requires_exception(self) -> bool:
        return self.nav.status in (
            ValidationStatus.BREACH, ValidationStatus.FAIL
        )


class ExceptionCell(BaseCell):
    """
    Fired by Randy when a ResultCell is BREACH or FAIL.
    human_decision_required is always True — blocks the workflow
    until a human records their decision.
    """
    cell_role: Literal[CellRole.EXCEPTION] = CellRole.EXCEPTION
    nav:       ExceptionNav

    human_decision_required: bool = True

    @model_validator(mode="after")
    def sync_nav_to_metadata(self) -> ExceptionCell:
        self.serialise_nav(self.nav)
        return self

    @property
    def is_resolved(self) -> bool:
        return self.nav.human_decision is not None

    def record_decision(
        self,
        decision: HumanDecision,
        rationale: str,
        reviewer: str,
    ) -> None:
        self.nav.human_decision = decision
        self.nav.decision_rationale = rationale
        self.nav.decision_by = reviewer
        self.nav.decision_at = datetime.utcnow()
        self.serialise_nav(self.nav)


class SignoffCell(BaseCell):
    """
    Human sign-off. document_hash is a cryptographic attestation
    that the document has not changed since it was reviewed.
    """
    cell_role: Literal[CellRole.SIGNOFF] = CellRole.SIGNOFF
    nav:       SignoffNav

    @model_validator(mode="after")
    def sync_nav_to_metadata(self) -> SignoffCell:
        self.serialise_nav(self.nav)
        return self

    def sign(self, reviewer: str, role: str, document_json: str) -> None:
        self.nav.reviewer = reviewer
        self.nav.reviewer_role = role
        self.nav.approved_at = datetime.utcnow()
        self.nav.document_hash = hashlib.sha256(
            document_json.encode()
        ).hexdigest()
        self.serialise_nav(self.nav)


# ── Discriminated union ───────────────────────────────────────────────────────
# `cell_role` is the discriminator — Pydantic reads it and routes to the
# correct concrete class in O(1) with no isinstance chains.

AnyCell = Annotated[
    Union[
        NarrativeCell,
        ReasoningCell,
        ValidationCell,
        ResultCell,
        ExceptionCell,
        SignoffCell,
    ],
    Field(discriminator="cell_role"),
]
