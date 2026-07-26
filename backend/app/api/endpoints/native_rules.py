"""JSON-first deterministic rules API (product path). Drools routes remain dormant."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.rules.engine import RuleEngine
from app.rules.loader import RuleLoader
from app.rules.registry import get_rule_registry

router = APIRouter(prefix="/rules", tags=["Native Rules"])


class NativeRuleEvaluateRequest(BaseModel):
    rule_family: str = Field(..., description="Indexed rule family id")
    version: str = Field(default="1.0.0", description="Rule definition version")
    facts: Dict[str, Any] = Field(..., description="Facts document for evaluation")


class NativeRuleEvaluateResponse(BaseModel):
    triggered: bool
    evaluation_status: str
    result: Dict[str, Any]


@router.get("/definitions", response_model=List[Dict[str, Any]])
async def list_native_rule_definitions() -> List[Dict[str, Any]]:
    """List versioned JSON rule definitions from the contracts registry."""
    loader = RuleLoader()
    definitions: List[Dict[str, Any]] = []
    for (rule_family, version), filename in sorted(loader.RULE_INDEX.items()):
        try:
            record = loader.load_rule(rule_family, version)
        except FileNotFoundError:
            continue
        payload = record.definition.get("payload", {})
        definitions.append(
            {
                "rule_family": rule_family,
                "version": version,
                "filename": filename,
                "rule_id": payload.get("rule_id", rule_family),
                "rule_name": payload.get("rule_name", rule_family),
                "status": payload.get("status", "unknown"),
                "expression_language": payload.get("expression_language"),
                "determinism_class": payload.get("determinism_class"),
                "description": payload.get("description", ""),
                "engine": "jsonlogic",
            }
        )
    return definitions


@router.post("/evaluate", response_model=NativeRuleEvaluateResponse)
async def evaluate_native_rule(
    request: NativeRuleEvaluateRequest,
) -> NativeRuleEvaluateResponse:
    """Evaluate facts against a JSON-first deterministic rule."""
    # Ensure the family is loadable before evaluating.
    registry = get_rule_registry()
    try:
        registry.get_rule(request.rule_family, request.version)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    engine = RuleEngine()
    outcome = engine.evaluate_rule(
        request.rule_family, request.version, request.facts
    )
    return NativeRuleEvaluateResponse(
        triggered=outcome.triggered,
        evaluation_status=outcome.evaluation_status,
        result=outcome.result,
    )
