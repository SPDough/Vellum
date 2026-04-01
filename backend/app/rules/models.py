"""Models for Vellum's lightweight JSON-first deterministic rule registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class RuleDefinitionRecord:
    rule_family: str
    version: str
    definition: Dict[str, Any]
    base_path: Path


@dataclass
class RuleEvaluationRequest:
    rule_family: str
    version: str
    facts: Dict[str, Any]
    evaluation_context: Optional[Dict[str, Any]] = None


@dataclass
class RuleEvaluationOutcome:
    triggered: bool
    evaluation_status: str
    result: Dict[str, Any]
