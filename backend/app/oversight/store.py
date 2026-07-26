"""In-memory store for the P0 oversight vertical slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OversightSnapshot:
    run_id: str = ""
    ran_at: str = ""
    positions: List[Dict[str, Any]] = field(default_factory=list)
    comparisons: List[Dict[str, Any]] = field(default_factory=list)
    rule_results: List[Dict[str, Any]] = field(default_factory=list)
    breaks: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class OversightStore:
    def __init__(self) -> None:
        self._snapshot = OversightSnapshot()

    def replace(self, snapshot: OversightSnapshot) -> OversightSnapshot:
        self._snapshot = snapshot
        return self._snapshot

    def get(self) -> OversightSnapshot:
        return self._snapshot

    def clear(self) -> None:
        self._snapshot = OversightSnapshot()


_STORE: Optional[OversightStore] = None


def get_oversight_store() -> OversightStore:
    global _STORE
    if _STORE is None:
        _STORE = OversightStore()
    return _STORE
