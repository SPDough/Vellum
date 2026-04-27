"""Pydantic schemas for procedure documents (NAV validation cell documents)."""

from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field


CellStatus = Literal["pass", "warn", "breach", "fail", "running", "pending"]
DocumentStatus = Literal["draft", "running", "awaiting_review", "signed", "rejected"]


class _BaseCell(BaseModel):
    cell_id: str
    position: int
    label: Optional[str] = None


class NarrativeCell(_BaseCell):
    cell_role: Literal["narrative"]
    body: str


class ReasoningCell(_BaseCell):
    cell_role: Literal["reasoning"]
    body: str
    collapsed_by_default: bool = False


class ValidationCell(_BaseCell):
    cell_role: Literal["validation"]
    rule_id: str
    status: CellStatus


class ResultMetric(BaseModel):
    label: str
    value: str


class ResultCell(_BaseCell):
    cell_role: Literal["result"]
    status: CellStatus
    summary: str
    metrics: Optional[List[ResultMetric]] = None


class RemediationOption(BaseModel):
    id: str
    label: str
    description: str


class ExceptionResolution(BaseModel):
    option_id: str
    rationale: str
    decided_by: str
    decided_at: str


class ExceptionCell(_BaseCell):
    cell_role: Literal["exception"]
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    remediation_options: List[RemediationOption]
    linked_result_cell_id: Optional[str] = None
    resolution: Optional[ExceptionResolution] = None


class SignoffCell(_BaseCell):
    cell_role: Literal["signoff"]
    required_role: str
    signed_by: Optional[str] = None
    signed_at: Optional[str] = None


Cell = Annotated[
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


class ProcedureDocument(BaseModel):
    id: str
    title: str
    fund_code: str
    as_of_date: str
    status: DocumentStatus
    cells: List[Cell]


class ExceptionDecisionRequest(BaseModel):
    option_id: str
    rationale: str


class ExceptionDecisionResponse(BaseModel):
    cell_id: str
    resolution: ExceptionResolution


class SignoffRequest(BaseModel):
    signed_by: str


class SignoffResponse(BaseModel):
    cell_id: str
    signed_by: str
    signed_at: str
