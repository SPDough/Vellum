import json
import pytest
from otomeshon.core.cells import (
    NarrativeCell, ReasoningCell, ValidationCell,
    ResultCell, ExceptionCell, SignoffCell,
    NarrativeNav, ReasoningNav, ValidationNav,
    ResultNav, ExceptionNav, SignoffNav,
    ProvenanceChain, ToolCallRecord, RemediationOption,
    AnyCell, CellRole, ValidationStatus, ExecutionMode,
    BreachType, HumanDecision,
)
from otomeshon.core.document import ProcedureDocument
from pydantic import TypeAdapter
from datetime import datetime

ADAPTER = TypeAdapter(AnyCell)


def make_provenance() -> ProvenanceChain:
    return ProvenanceChain(
        prompt_hash=ProvenanceChain.compute_prompt_hash("test prompt"),
        model_id="claude-sonnet-4-6",
        agent_id="nav-validator-v1.2",
        agent_version="1.2.0",
        token_count=450,
        data_hash=ProvenanceChain.compute_data_hash({"fund": "FUND001"}),
        tool_calls=[
            ToolCallRecord(
                tool_name="compare_nav_components",
                mcp_server="nav-validation-server",
                params={"fund_id": "FUND001", "date": "2026-04-27"},
                result_hash="abc123",
                duration_ms=342,
                success=True,
            )
        ],
    )


@pytest.mark.parametrize("cell_cls,nav_cls,role,nav_kwargs", [
    (NarrativeCell, NarrativeNav, CellRole.NARRATIVE,
     {"step_owner": "fund_controller"}),
    (ReasoningCell, ReasoningNav, CellRole.REASONING,
     {"chain_of_thought": "reviewing accrued income",
      "confidence_score": 0.92,
      "provenance": make_provenance()}),
    (ValidationCell, ValidationNav, CellRole.VALIDATION,
     {"mcp_tool": "compare_nav_components",
      "mcp_server": "nav-validation-server",
      "mcp_params": {"fund_id": "FUND001"},
      "execution_mode": ExecutionMode.SUPERVISED}),
    (ResultCell, ResultNav, CellRole.RESULT,
     {"status": ValidationStatus.PASS,
      "run_id": "run_test_001",
      "data_hash": "deadbeef",
      "result_delta": 127.50}),
    (ExceptionCell, ExceptionNav, CellRole.EXCEPTION,
     {"breach_type": BreachType.TOLERANCE_EXCEEDED,
      "breach_magnitude": "4.2bps vs 0.5bps",
      "triggering_run_id": "run_test_001",
      "agent_diagnosis": "likely timing difference",
      "confidence_in_diagnosis": 0.82,
      "remediation_options": [
          RemediationOption(
              option=HumanDecision.ACCEPT_WITH_NOTE,
              label="Accept — timing",
              description="Accept delta as T+1 timing diff",
          )
      ]}),
    (SignoffCell, SignoffNav, CellRole.SIGNOFF,
     {"reviewer": "SDoug", "reviewer_role": "fund_controller"}),
])
def test_cell_roundtrip(cell_cls, nav_cls, role, nav_kwargs):
    nav = nav_cls(step="3.2", step_label="Accrued income", **nav_kwargs)
    cell = cell_cls(position=0, step_id="3.2", nav=nav)

    # Verify cell_role discriminator
    assert cell.cell_role == role

    # Serialise → deserialise via discriminated union
    raw = cell.model_dump(mode="json")
    restored = ADAPTER.validate_python(raw)

    assert restored.cell_role == cell.cell_role
    assert restored.cell_id == cell.cell_id
    assert restored.get_nav_raw() == cell.get_nav_raw()


def test_document_roundtrip():
    doc = ProcedureDocument(
        procedure_name="NAV Validation — Daily",
        procedure_version="2.1.0",
        fund_id="FUND001",
        valuation_date="2026-04-27",
        custodian="State Street",
    )
    nav = NarrativeNav(step="1.0", step_label="Scope",
                       step_owner="fund_controller")
    doc.append_cell(NarrativeCell(position=0, step_id="1.0", nav=nav))

    raw = doc.to_json()
    restored = ProcedureDocument.from_json(raw)

    assert restored.doc_id == doc.doc_id
    assert len(restored.cells) == 1
    assert restored.cells[0].cell_role == CellRole.NARRATIVE


def test_exception_blocks_signoff():
    doc = ProcedureDocument(
        procedure_name="test", procedure_version="1.0",
        fund_id="F1", valuation_date="2026-04-27", custodian="SS",
    )
    exc_nav = ExceptionNav(
        step="3.2", step_label="Income",
        breach_type=BreachType.TOLERANCE_EXCEEDED,
        breach_magnitude="5bps", triggering_run_id="r1",
        agent_diagnosis="TBD", confidence_in_diagnosis=0.8,
    )
    doc.append_cell(ExceptionCell(position=0, step_id="3.2", nav=exc_nav))
    assert not doc.is_ready_for_signoff()
