"""Scoreboard read and dashboard vital tests.

Agent: surfaces
Role: prove the vital prints the reporter's numbers, never zeros, for the selected run.
External I/O: none; graph is in-memory and AzureReader is fake.
"""

from __future__ import annotations

import pytest

from kernel import InMemoryGraphStore
from surfaces.dashboard.projections_performance import (
    performance_tone,
    performance_vital,
)
from surfaces.dashboard.projections_vitals import vitals_projection
from surfaces.dashboard.settings import DashboardSettings
from surfaces.queries.performance import PERFORMANCE_KEYS, run_performance
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.performance_fixtures import MEASURED, seed_run, with_excess
from surfaces.tests.test_dashboard_costs import _settings

_MINUS = chr(0x2212)  # the typographic minus the operator reads


def test_a1_run_performance_reads_the_reporters_numbers_unchanged() -> None:
    """RPT-OUT-07 / SRF-OUT-07: all 12 values equal the Snapshot's, unchanged."""
    graph = InMemoryGraphStore()
    seed_run(graph, "sched-2026-09-24", performance=dict(MEASURED))

    view = run_performance(graph, "sched-2026-09-24")

    assert view.status == "measured"
    assert set(PERFORMANCE_KEYS) == set(MEASURED)
    assert dict(view.metrics) == MEASURED
    assert view.benchmark == "SPY"


def test_a2_a_run_behind_by_028_is_amber_with_the_plain_line() -> None:
    """SRF-OUT-07 / DL-220: -0.28 pts at the default red line is amber."""
    graph = InMemoryGraphStore()
    seed_run(graph, "sched-2026-09-24", performance=dict(MEASURED))

    vital = performance_vital(graph, "sched-2026-09-24", DashboardSettings())

    assert vital["tone"] == "warn"
    assert vital["text"] == f"vs SPY {_MINUS}0.28 pts · 32 sessions · 21 % invested"


def test_a3_a_run_without_the_group_reads_unavailable_not_zero() -> None:
    """RPT-FAIL-04 / SRF-OUT-07: a pre-scoreboard run renders no number at all."""
    graph = InMemoryGraphStore()
    seed_run(graph, "old-run", performance=None)

    view = run_performance(graph, "old-run")
    vital = performance_vital(graph, "old-run", DashboardSettings())

    assert view.status == "unavailable"
    assert dict(view.metrics) == {}
    assert vital["tone"] == "idle"
    assert vital["text"] == "no scoreboard for this run"
    assert "detail" not in vital
    assert "0.00" not in str(vital)


def test_a3_a_partial_group_and_a_missing_snapshot_read_unavailable() -> None:
    """RPT-FAIL-04 / SRF-OUT-07: a missing key or report is unavailable, not zero."""
    graph = InMemoryGraphStore()
    partial = {k: v for k, v in MEASURED.items() if k != "excess_return_pct"}
    seed_run(graph, "partial", performance=partial)
    seed_run(graph, "bad-type", performance={**MEASURED, "excess_return_pct": True})
    seed_run(graph, "unreported", with_snapshot=False)

    for run_id in ("partial", "bad-type", "unreported", "no-such-run", ""):
        view = run_performance(graph, run_id)
        assert (view.status, dict(view.metrics)) == ("unavailable", {}), run_id
        assert view.reason


def test_a4_zero_sessions_reads_no_sessions() -> None:
    """RPT-FAIL-04 / SRF-OUT-07: the reporter's empty-metrics dict is no_sessions."""
    graph = InMemoryGraphStore()
    empty = dict.fromkeys(MEASURED, 0.0)
    seed_run(graph, "empty", performance=empty)

    view = run_performance(graph, "empty")
    vital = performance_vital(graph, "empty", DashboardSettings())

    assert view.status == "no_sessions"
    assert vital["tone"] == "idle"
    assert vital["text"] == "no scoreboard sessions yet"
    assert "detail" not in vital


def test_a5_the_snapshot_is_found_by_the_chain_not_by_run_id() -> None:
    """SRF-OUT-07: the key is snapshot:pm-run-<hex>; snapshot:<run_id> is absent."""
    graph = InMemoryGraphStore()
    key = seed_run(graph, "sched-2026-09-24", performance=dict(MEASURED))

    assert key.startswith("snapshot:pm-run-")
    assert graph.get_node("Snapshot", "snapshot:sched-2026-09-24") is None
    assert run_performance(graph, "sched-2026-09-24").status == "measured"


@pytest.mark.parametrize(
    ("excess", "tone"),
    [
        (0.0, "good"),
        (-0.0, "good"),
        (-0.004, "good"),
        (0.01, "good"),
        (-0.99, "warn"),
        (-1.0, "crit"),
        (-1.01, "crit"),
    ],
)
def test_a6_tone_boundaries_at_the_default_red_line(excess: float, tone: str) -> None:
    """SRF-OUT-07 / DL-220: green >= 0, red <= -1.00, amber between, on the display."""
    assert performance_tone(excess, DashboardSettings()) == tone


def test_a6_moving_the_red_line_moves_the_tone() -> None:
    """SRF-OUT-07 / DL-220: the red line is a setting, not a literal."""
    tighter = DashboardSettings(performance_behind_threshold_pts=0.5)
    assert performance_tone(-0.99, tighter) == "crit"
    assert performance_tone(-0.49, tighter) == "warn"


def test_a7_the_vital_follows_the_selected_run() -> None:
    """SRF-OUT-01 / SRF-OUT-07: the vital scopes to the selected run, not the latest."""
    graph = InMemoryGraphStore()
    seed_run(graph, "older", performance=with_excess(0.42))
    seed_run(
        graph,
        "newer",
        performance=with_excess(-1.5),
        requested_at="2026-09-25T22:30:00+00:00",
    )
    settings, azure = _settings(), FakeAzureReader()

    older = vitals_projection(graph, azure, settings, "older")["performance"]
    latest = vitals_projection(graph, azure, settings, None)["performance"]

    assert (older["run_id"], older["tone"]) == ("older", "good")  # type: ignore[index]
    assert (latest["run_id"], latest["tone"]) == ("newer", "crit")  # type: ignore[index]


def test_the_benchmark_name_comes_from_the_reporters_headline() -> None:
    """SRF-OUT-07 / DL-220: no literal benchmark; unnamed reads as the market."""
    graph = InMemoryGraphStore()
    seed_run(graph, "named", performance=dict(MEASURED), headline="x. vs QQQ: 1 pts")
    seed_run(graph, "unnamed", performance=dict(MEASURED), headline="no clause")

    assert run_performance(graph, "named").benchmark == "QQQ"
    assert run_performance(graph, "unnamed").benchmark is None
    text = performance_vital(graph, "unnamed", DashboardSettings())["text"]
    assert str(text).startswith(f"vs the market {_MINUS}0.28 pts")
