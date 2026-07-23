"""Dashboard UNPROVEN light tests — visible without being alarming (DL-59).

Agent: surfaces
Role: an unresolved run stays GREEN (no fault) but always carries a warning row and
      a summary saying nothing filled; a real fault still turns it RED.
External I/O: none; all projections are fakes.
"""

from __future__ import annotations

import surfaces.dashboard.projections_verdict as projection
from surfaces.tests.test_dashboard_verdict import _acceptance, _stages, _vitals


def test_unproven_stays_green_but_never_reads_as_a_clean_pass() -> None:
    """DL-59: orders queued for the open are not a fault, so the light stays GREEN —
    a nightly false RED trains the operator to ignore it. It must still be visibly
    unproven: a warning row and a summary that says nothing filled."""
    stages = _stages()
    stages[4]["observed"] = {"submitted": 5, "orders": 5, "filled": 0, "unfilled": 0}

    result = projection.project_verdict(
        _acceptance("UNPROVEN", warning=False),
        stages,
        _vitals(fault=False, warning=False),
        {"escalations": []},
    )

    assert result["light"] == "GREEN"
    assert result["summary"] == "5 orders placed, none filled yet"
    assert result["warning_count"] == 1
    warnings = result["warnings"]
    assert isinstance(warnings, list)
    assert warnings[0]["code"] == "orders_unresolved"


def test_unproven_with_a_real_fault_is_still_red() -> None:
    """An unresolved run does not mask an actual fault."""
    result = projection.project_verdict(
        _acceptance("UNPROVEN", warning=False),
        _stages(),
        _vitals(fault=True, warning=False),
        {"escalations": []},
    )

    assert result["light"] == "RED"
