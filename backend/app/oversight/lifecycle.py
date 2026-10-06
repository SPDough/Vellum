"""Break control-loop statuses — backend owns official state (P3 moat)."""

from __future__ import annotations

from typing import Dict, Set

BREAK_STATUSES = ("open", "acknowledged", "in_review", "resolved", "dismissed")

# Who may move where — machine-enforced, not portal opinion.
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "open": {"acknowledged", "in_review", "resolved", "dismissed"},
    "acknowledged": {"in_review", "resolved", "dismissed", "open"},
    "in_review": {"resolved", "acknowledged", "dismissed"},
    "resolved": {"open"},
    "dismissed": {"open"},
}


class BreakTransitionError(ValueError):
    pass


def assert_transition(current: str, new_status: str) -> None:
    current_norm = (current or "open").lower()
    new_norm = (new_status or "").lower()
    if new_norm not in BREAK_STATUSES:
        raise BreakTransitionError(f"Unknown break status: {new_status}")
    allowed = ALLOWED_TRANSITIONS.get(current_norm, set())
    if new_norm not in allowed:
        raise BreakTransitionError(
            f"Illegal transition {current_norm!r} -> {new_norm!r}"
        )
