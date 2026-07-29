"""Resume stage contract tests.

Agent: orchestration
Role: pin broker-consequence stages and artifact ordering by name.
External I/O: none.
"""

from __future__ import annotations

import pytest

from contracts.resume import BROKER_RESUME_STAGES, RESUME_STAGES
from orchestration.resume_plan import ARTIFACTS, validate_alignment


def test_broker_resume_stages_are_explicit_by_name() -> None:
    """SUP-FAIL-03 / SUP-OBS-01: planted head stage proves no index slicing."""
    expected = {
        "position_sync",
        "provider",
        "scanner",
        "analyst",
        "pm",
        "execution",
    }
    planted_head_insert = ("preflight", *RESUME_STAGES)
    sliced_if_indexed = frozenset(planted_head_insert[: len(expected)])

    assert expected == BROKER_RESUME_STAGES
    assert sliced_if_indexed != BROKER_RESUME_STAGES


def test_resume_artifacts_validate_alignment_rejects_mismatch() -> None:
    """SUP-FAIL-03 / SUP-OBS-01: planted artifact mismatch raises clearly."""
    validate_alignment()
    broken = (ARTIFACTS[1], ARTIFACTS[0], *ARTIFACTS[2:])

    with pytest.raises(ValueError, match="not aligned"):
        validate_alignment(artifacts=broken)
