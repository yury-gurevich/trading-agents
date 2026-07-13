"""Dashboard master-light truth table and deterministic summary tests.

Agent: surfaces
Role: prove PASS/NO_TRADE/FAIL across fault and warning classes using fake reads.
External I/O: none; the graph store and all downstream projections are fakes.
"""

from __future__ import annotations

import pytest

import surfaces.dashboard.projections_verdict as projection
from kernel import InMemoryGraphStore
from surfaces.tests.test_dashboard_costs import _settings


def _acceptance(verdict: str, *, warning: bool) -> dict[str, object]:
    breaches: list[dict[str, object]] = []
    if warning:
        breaches.append(
            {
                "stage": "provider",
                "key": "sector_coverage",
                "detail": "Sector coverage is unavailable",
                "severity": "warn",
            }
        )
    return {
        "run_id": "truth",
        "verdict": verdict,
        "passed": verdict != "FAIL",
        "breaches": breaches,
        "no_trade_day": verdict == "NO_TRADE",
        "confidence_bar": 0.6,
        "annotation": None,
    }


def _stages(*, complete: bool = True) -> list[dict[str, object]]:
    names = ("provider", "scanner", "analyst", "pm", "execution", "monitor", "reporter")
    return [
        {
            "name": name,
            "reached": complete or name != "reporter",
            "observed": (
                {"scored": 0, "rejected": 5}
                if name == "analyst"
                else {"submitted": 0}
                if name == "execution"
                else {}
            ),
        }
        for name in names
    ]


def _vitals(*, fault: bool, warning: bool) -> dict[str, object]:
    return {
        "spine": {"status": "unavailable" if fault else "reachable"},
        "bus": {"status": "reachable"},
        "pending_flags": 1 if warning else 0,
        "degraded_feeds": {"count": 0},
        "mtd_cost": {"untracked_llm_models": []},
        "next_fire": "2026-07-11T22:30:00+00:00",
    }


@pytest.mark.parametrize("verdict", ["PASS", "NO_TRADE", "FAIL"])
@pytest.mark.parametrize("fault", [False, True])
@pytest.mark.parametrize("warning", [False, True])
def test_full_master_light_truth_table_with_fake_store(
    monkeypatch: pytest.MonkeyPatch, verdict: str, fault: bool, warning: bool
) -> None:
    graph = InMemoryGraphStore()
    monkeypatch.setattr(
        projection,
        "run_verdict",
        lambda graph, run: _acceptance(verdict, warning=warning),
    )
    monkeypatch.setattr(projection, "run_stages", lambda graph, run: _stages())
    monkeypatch.setattr(
        projection,
        "vitals_projection",
        lambda graph, azure, settings, run, now=None: _vitals(
            fault=fault, warning=warning
        ),
    )
    monkeypatch.setattr(
        projection,
        "run_recovery",
        lambda graph, run: {"escalations": [], "remediation_plans": []},
    )

    result = projection.verdict_projection(graph, "truth", None, _settings())

    assert result["light"] == (
        "GREEN" if verdict in {"PASS", "NO_TRADE"} and not fault else "RED"
    )
    warning_count = result["warning_count"]
    assert isinstance(warning_count, int)
    assert (warning_count > 0) is warning


def test_no_trade_summary_and_warning_rows_are_plain_language() -> None:
    result = projection.project_verdict(
        _acceptance("NO_TRADE", warning=False),
        _stages(),
        _vitals(fault=False, warning=True),
        {"escalations": []},
    )
    assert result["light"] == "GREEN"
    assert result["summary"] == "5 candidates below confidence bar (0.6)"
    assert result["warning_count"] == 1


def test_pass_summary_is_compact_and_pluralized() -> None:
    stages = _stages()
    stages[2]["observed"] = {"scored": 3, "rejected": 0}
    stages[4]["observed"] = {"submitted": 3}

    result = projection.project_verdict(
        _acceptance("PASS", warning=False),
        stages,
        _vitals(fault=False, warning=False),
        {"escalations": []},
    )

    assert result["summary"] == "3 orders, 3 candidates"

    stages[2]["observed"] = {"scored": 1, "rejected": 0}
    stages[4]["observed"] = {"submitted": 1}
    singular = projection.project_verdict(
        _acceptance("PASS", warning=False),
        stages,
        _vitals(fault=False, warning=False),
        {"escalations": []},
    )
    assert singular["summary"] == "1 order, 1 candidate"


def test_stalled_stage_and_operator_hold_are_red() -> None:
    stalled = projection.project_verdict(
        _acceptance("FAIL", warning=False),
        _stages(complete=False),
        _vitals(fault=False, warning=False),
        {"escalations": []},
    )
    assert stalled["light"] == "RED"
    assert "reporter" in str(stalled["summary"])
    held = projection.project_verdict(
        _acceptance("PASS", warning=False),
        _stages(),
        _vitals(fault=False, warning=False),
        {"escalations": [{"status": "open"}]},
    )
    assert held["light"] == "RED"
    assert "operator" in str(held["summary"])


def test_degraded_feeds_and_untracked_spend_are_warning_rows() -> None:
    acceptance = _acceptance("PASS", warning=False)
    acceptance["breaches"] = ()
    vitals = _vitals(fault=False, warning=False)
    vitals["degraded_feeds"] = {"count": 2}
    vitals["mtd_cost"] = {"untracked_llm_models": ["unknown-model"]}
    result = projection.project_verdict(
        acceptance, _stages(), vitals, {"escalations": []}
    )
    assert result["light"] == "GREEN"
    assert result["warning_count"] == 2
    acceptance["breaches"] = [None]
    no_warning = projection.project_verdict(
        acceptance, _stages(), _vitals(fault=False, warning=False), {"escalations": []}
    )
    assert no_warning["warning_count"] == 0
