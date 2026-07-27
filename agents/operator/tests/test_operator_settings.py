"""Operator settings tests.

Agent: operator
Role: verify the reasoning-depth and output-ceiling tunables and their bounds.
External I/O: none.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agents.operator.settings import OperatorSettings


def test_effort_defaults_to_max() -> None:
    assert OperatorSettings().effort == "max"


def test_max_tokens_leaves_room_for_effort_driven_thinking() -> None:
    """512 is spent reasoning before a tool call is emitted (OPR-PERF-01)."""
    assert OperatorSettings().max_tokens == 4096


@pytest.mark.parametrize("level", ["low", "medium", "high", "xhigh", "max"])
def test_effort_accepts_every_rung_of_the_api_ladder(
    level: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPERATOR_EFFORT", level)
    assert OperatorSettings().effort == level


def test_effort_rejects_a_level_the_model_would_refuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail on load, not on a 400 from the API mid-run."""
    monkeypatch.setenv("OPERATOR_EFFORT", "maximum")
    with pytest.raises(ValidationError):
        OperatorSettings()
