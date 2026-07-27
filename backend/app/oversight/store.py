"""In-memory snapshot shape for oversight runs (P0/P1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class OversightSnapshot:
    run_id: str = ""
    ran_at: str = ""
    positions: List[Dict[str, Any]] = field(default_factory=list)
    comparisons: List[Dict[str, Any]] = field(default_factory=list)
    rule_results: List[Dict[str, Any]] = field(default_factory=list)
    breaks: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
