"""The supervisor's last successful run is the newest reported graph-pull run.

Agent: supervisor
Role: prove last_successful_run orders by the PMRun's time and names the run id.
External I/O: none.
"""

from __future__ import annotations

from agents.supervisor.domain.health import compute_health
from kernel import InMemoryGraphStore

_EDGES = (
    ("INGESTED_BY", "MarketData"),
    ("SCANNED_BY", "ScanRun"),
    ("ANALYZED_BY", "AnalystRun"),
    ("EVALUATED_BY", "PMRun"),
    ("EXECUTED_BY", "ExecutionRun"),
    ("MONITORED_BY", "MonitorRun"),
)


def _chain(graph: InMemoryGraphStore, run_id: str, pm_key: str, pm_at: str) -> None:
    parent = graph.merge_node("RunRequest", f"run-request:{run_id}", {"run_id": run_id})
    for edge, label in _EDGES:
        key = pm_key if label == "PMRun" else f"{label}:{run_id}"
        props = {"created_at": pm_at} if label == "PMRun" else {}
        child = graph.merge_node(label, key, props)
        graph.add_edge(parent, child, edge)
        parent = child
    snapshot = graph.merge_node("Snapshot", f"snapshot:{pm_key}", {"run_id": pm_key})
    graph.add_edge(parent, snapshot, "REPORTED_BY")


def test_last_successful_run_is_ordered_by_pm_run_time_not_by_key() -> None:
    """SUP-OUT-02: the newest PMRun wins, however the Snapshot keys sort."""
    graph = InMemoryGraphStore()
    # "pm-run-ff…" sorts after "pm-run-00…", but it is the older run.
    _chain(graph, "sched-old", "pm-run-ff", "2026-09-23T22:41:00+00:00")
    _chain(graph, "sched-new", "pm-run-00", "2026-09-24T22:41:00+00:00")
    # A legacy verify Snapshot with no PMRun and no time must not win on its key.
    graph.merge_node("Snapshot", "snapshot:verify-zzz", {"run_id": "verify-zzz"})

    assert compute_health(graph, None)["last_successful_run"] == "sched-new"


def test_a_snapshot_with_no_run_request_is_named_by_its_key() -> None:
    """SUP-OUT-02: without a RunRequest upstream, the Snapshot key is the name."""
    graph = InMemoryGraphStore()
    graph.merge_node("PMRun", "pm-run-a", {"created_at": "2026-09-24T22:41:00+00:00"})
    graph.merge_node("Snapshot", "snapshot:pm-run-a", {"run_id": "pm-run-a"})

    assert compute_health(graph, None)["last_successful_run"] == "snapshot:pm-run-a"
