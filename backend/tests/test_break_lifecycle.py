"""Unit tests for break control-loop transition rules."""

from __future__ import annotations

import pytest

from app.oversight.lifecycle import BreakTransitionError, assert_transition


def test_legal_open_to_acknowledged():
    assert_transition("open", "acknowledged")


def test_illegal_resolved_to_acknowledged():
    with pytest.raises(BreakTransitionError):
        assert_transition("resolved", "acknowledged")


def test_reopen_from_resolved():
    assert_transition("resolved", "open")
