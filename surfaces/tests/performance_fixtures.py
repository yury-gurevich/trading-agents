"""Run-chain fixtures carrying the reporter's performance scoreboard.

Agent: surfaces
Role: seed a RunRequest -> ... -> Snapshot chain keyed like production graph-pull runs.
External I/O: none; writes only to the supplied in-memory graph.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from orchestration.batch_chain import CHAIN

if TYPE_CHECKING:
    from kernel import GraphStore

# sched-2026-09-24's Snapshot, measured on the live spine 2026-09-25 (S228 spec).
MEASURED: dict[str, float] = {
    "portfolio_return_pct": -0.4523,
    "benchmark_return_pct": -0.9094,
    "exposure_matched_return_pct": -0.1737,
    "excess_return_pct": -0.2787,
    "average_exposure_pct": 21.19,
    "max_drawdown_pct": -0.9392,
    "rolling_portfolio_return_pct": -0.7629,
    "rolling_exposure_matched_return_pct": -0.1737,
    "rolling_excess_return_pct": -0.5892,
    "performance_sessions": 32.0,
    "performance_gap_sessions": 0.0,
    "equity_cents": 10200072.0,
}
HEADLINE = (
    "0 positions opened; 0 closed; 26 recommendations stitched. "
    "vs SPY: -0.28 pts over 32 sessions at 21% invested"
)
_OTHER_GROUPS: dict[str, dict[str, float]] = {
    "portfolio": {"positions_opened": 0.0, "positions_closed": 0.0},
    "signal": {"recommendation_count": 26.0},
    "regime": {"vix": 14.8},
}


def seed_run(
    graph: GraphStore,
    run_id: str,
    *,
    performance: dict[str, float] | None = None,
    requested_at: str = "2026-09-24T22:30:00+00:00",
    headline: str = HEADLINE,
    with_snapshot: bool = True,
) -> str:
    """Seed one chain; return the Snapshot key (``snapshot:pm-run-<hex>``)."""
    hex_id = hashlib.sha256(run_id.encode()).hexdigest()[:8]
    parent = graph.merge_node(
        "RunRequest",
        f"run-request:{run_id}",
        {"run_id": run_id, "requested_at": requested_at},
    )
    for edge, label in CHAIN:
        if label == "Snapshot":
            break
        key = f"pm-run-{hex_id}" if label == "PMRun" else f"{label}:{run_id}"
        child = graph.merge_node(label, key, {"run_id": run_id})
        graph.add_edge(parent, child, edge)
        parent = child
    snapshot_key = f"snapshot:pm-run-{hex_id}"
    if with_snapshot:
        metrics: dict[str, dict[str, float]] = dict(_OTHER_GROUPS)
        if performance is not None:
            metrics["performance"] = performance
        snapshot = graph.merge_node(
            "Snapshot",
            snapshot_key,
            {
                "run_id": f"pm-run-{hex_id}",
                "metrics": metrics,
                "headline_summary": headline,
            },
        )
        graph.add_edge(parent, snapshot, "REPORTED_BY")
    return snapshot_key


def with_excess(excess: float) -> dict[str, float]:
    """Return the measured scoreboard with a different since-inception excess."""
    return {**MEASURED, "excess_return_pct": excess}
