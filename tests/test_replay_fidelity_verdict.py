"""S237 A6: the verdict follows DL-237 as amended (R5), over clean sessions only.

Agent: tooling
Role: prove the per-stage agreement bar, the floors and the unexplained rule.
External I/O: none.
"""

from __future__ import annotations

from typing import Any

import pytest
from scripts.replay_fidelity_verdict import compute_verdict


def _units(
    stage: str,
    matching: int,
    differing: int,
    *,
    cause: str = "not_persisted:benchmark",
    judged: bool = True,
    clean: bool = True,
    sessions: int = 4,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index in range(matching + differing):
        match = index < matching
        out.append(
            {
                "session": f"2026-10-0{1 + index % sessions}",
                "stage": stage,
                "ticker": f"{stage[:2].upper()}{index:03d}",
                "field": "decision",
                "live": "x",
                "replay": "x" if match else "y",
                "match": match,
                "judged": judged,
                "cause": "" if match else cause,
                "clean": clean,
            }
        )
    return out


def _passing_neighbours() -> list[dict[str, Any]]:
    return _units("scanner", 20, 0) + _units("pm", 10, 0)


@pytest.mark.parametrize(
    ("matching", "differing", "verdict"),
    [(89, 11, "FAIL"), (90, 10, "PASS"), (99, 0, "INSUFFICIENT")],
    ids=["89-percent", "90-percent", "below-the-floor"],
)
def test_a6_the_verdict_follows_dl237(
    matching: int, differing: int, verdict: str
) -> None:
    """ANLZ-IDM-01: 89 % fails, 90 % passes, 99 tickers are insufficient."""
    rows = _passing_neighbours() + _units("analyst", matching, differing)

    summary = compute_verdict(rows, scanner_sessions=4)

    assert summary["verdict"] == verdict
    assert summary["stages"]["analyst"]["units"] == matching + differing
    assert summary["stages"]["analyst"]["matches"] == matching


def test_a6_an_unexplained_clean_difference_fails_whatever_the_percentage() -> None:
    """ANLZ-IDM-01 / DL-237: one unexplained clean difference is FAIL at 99 %."""
    rows = _passing_neighbours() + _units(
        "analyst", 99, 1, cause="unexplained", sessions=4
    )

    summary = compute_verdict(rows, scanner_sessions=4)

    assert summary["stages"]["analyst"]["agreement"] == pytest.approx(0.99)
    assert summary["unexplained"] == 1
    assert summary["verdict"] == "FAIL"


def test_an_unexplained_diagnostic_difference_also_fails() -> None:
    """SCAN-IDM-01: DL-237 asks for zero unexplained differences, not only judged."""
    rows = (
        _passing_neighbours()
        + _units("analyst", 100, 0)
        + _units("analyst", 0, 1, cause="unexplained", judged=False)
    )

    assert compute_verdict(rows, scanner_sessions=4)["verdict"] == "FAIL"


def test_non_clean_sessions_and_passthroughs_are_never_pooled() -> None:
    """PM-OUT-03: passthroughs are counted beside the PM bar; non-clean is beside."""
    rows = (
        _passing_neighbours()
        + _units("analyst", 100, 0)
        + _units("analyst", 0, 50, cause="unexplained", clean=False)
        + _units("pm", 0, 5, judged=False)
    )

    summary = compute_verdict(rows, scanner_sessions=4)

    assert summary["verdict"] == "PASS"
    assert summary["stages"]["analyst"]["units"] == 100
    assert summary["stages"]["pm"]["units"] == 10
    assert summary["stages"]["pm"]["hold_passthrough"] == {"units": 5, "matches": 0}


@pytest.mark.parametrize(
    ("scanner_sessions", "pm_units", "verdict"),
    [(3, 10, "INSUFFICIENT"), (4, 9, "INSUFFICIENT"), (4, 10, "PASS")],
    ids=["scanner-floor", "pm-floor", "both-floors-met"],
)
def test_every_stage_has_its_floor(
    scanner_sessions: int, pm_units: int, verdict: str
) -> None:
    """PM-IDM-01 / SCAN-IDM-01: scanner >= 4 sessions, PM >= 10 judged."""
    rows = (
        _units("scanner", 20, 0) + _units("pm", pm_units, 0) + _units("analyst", 100, 0)
    )

    summary = compute_verdict(rows, scanner_sessions=scanner_sessions)

    assert summary["verdict"] == verdict


def test_a_stage_under_the_bar_fails_even_below_its_floor() -> None:
    """PM-IDM-01 / R5: FAIL is decided before INSUFFICIENT."""
    rows = _units("scanner", 20, 0) + _units("analyst", 100, 0) + _units("pm", 1, 1)

    summary = compute_verdict(rows, scanner_sessions=4)

    assert summary["stages"]["pm"]["agreement"] == 0.5
    assert summary["verdict"] == "FAIL"
