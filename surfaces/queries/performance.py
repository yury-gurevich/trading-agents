"""Read-side query for the reporter's benchmark scoreboard on a run.

Agent: surfaces
Role: find a run's Snapshot through the run chain and read its performance group as is.
External I/O: injected GraphStore reads only.

The numbers are the reporter's (RPT-OUT-07). This module rounds nothing and computes
nothing; a missing or partial group is `unavailable`, never zeros (DL-220).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from orchestration.batch_chain import walk_chain

if TYPE_CHECKING:
    from kernel import GraphStore

PerformanceStatus = Literal["measured", "no_sessions", "unavailable"]

# The keys agents/reporter/domain/performance.py writes (RPT-OUT-07).
PERFORMANCE_KEYS = (
    "portfolio_return_pct",
    "benchmark_return_pct",
    "exposure_matched_return_pct",
    "excess_return_pct",
    "average_exposure_pct",
    "max_drawdown_pct",
    "rolling_portfolio_return_pct",
    "rolling_exposure_matched_return_pct",
    "rolling_excess_return_pct",
    "performance_sessions",
    "performance_gap_sessions",
    "equity_cents",
)
# The reporter names its benchmark only in the headline clause "vs SPY: ...".
_BENCHMARK = re.compile(r"\bvs ([A-Z][A-Z0-9.\-]{0,9}):")


@dataclass(frozen=True)
class PerformanceView:
    """One run's scoreboard as the reporter stored it, or why there is none."""

    run_id: str
    status: PerformanceStatus
    reason: str = ""
    benchmark: str | None = None
    metrics: Mapping[str, float] = field(default_factory=dict)


def run_performance(graph: GraphStore, run_id: str) -> PerformanceView:
    """Return the run's scoreboard; the Snapshot is found through the run chain."""
    snapshot = walk_chain(graph, run_id).get("Snapshot") if run_id else None
    if snapshot is None:
        return PerformanceView(run_id, "unavailable", "this run has no report yet")
    metrics = snapshot.props.get("metrics")
    group = metrics.get("performance") if isinstance(metrics, Mapping) else None
    if not isinstance(group, Mapping):
        reason = "this run was reported before the scoreboard existed"
        return PerformanceView(run_id, "unavailable", reason)
    values = {key: group.get(key) for key in PERFORMANCE_KEYS}
    missing = sorted(key for key, value in values.items() if not _is_number(value))
    if missing:
        reason = f"the scoreboard is incomplete ({', '.join(missing)})"
        return PerformanceView(run_id, "unavailable", reason)
    numbers = {key: float(value) for key, value in values.items()}  # type: ignore[arg-type]
    benchmark = _benchmark(snapshot.props.get("headline_summary"))
    if numbers["performance_sessions"] == 0:
        reason = "the reporter found no usable sessions"
        return PerformanceView(run_id, "no_sessions", reason, benchmark)
    return PerformanceView(run_id, "measured", "", benchmark, numbers)


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _benchmark(headline: object) -> str | None:
    match = _BENCHMARK.search(headline) if isinstance(headline, str) else None
    return match.group(1) if match else None
