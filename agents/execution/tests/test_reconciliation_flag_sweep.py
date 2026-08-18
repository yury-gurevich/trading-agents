"""Legacy divergence-flag sweep tests.

Agent: execution
Role: prove the pre-S178 snapshot-keyed flags are retired only by the sweep, are
      retired exactly once, and that a mis-keyed flag is left visibly open.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.reconciliation_flags import (
    record_divergences,
    resolve_legacy_flags,
    subject_ref_for,
)
from agents.execution.reconciliation_store import Divergence
from kernel import GraphStore, InMemoryGraphStore, Node

_PFE = Divergence("missing_graph_position", "PFE", "broker_qty=38")
_LEGACY = "broker-position-divergence:broker-position-snapshot:sched-1:t0"


def _snapshot(graph: GraphStore, key: str) -> Node:
    return graph.merge_node("BrokerPositionSnapshot", key, {"holding_count": 0})


def _legacy_flag(
    graph: GraphStore, subject: str, key_severity: str, **props: object
) -> None:
    graph.merge_node(
        "Flag",
        f"flag:{subject}:{key_severity}",
        {"subject_ref": subject, "status": "pending", **props},
    )


def test_a_run_leaves_legacy_and_foreign_flags_alone() -> None:
    """EXEC-TRG-07: only the sweep retires pre-S178 snapshot-keyed flags."""
    graph = InMemoryGraphStore()
    _legacy_flag(graph, _LEGACY, "critical", severity="critical")
    graph.merge_node(
        "Flag",
        "flag:predictor:x:info",
        {"subject_ref": "predictor:x", "severity": "info", "status": "pending"},
    )

    record_divergences(graph, snapshot=_snapshot(graph, "s1"), divergences=())

    assert graph.list_nodes("FlagResolution") == ()


def test_the_sweep_retires_legacy_flags_once_and_only_legacy_ones() -> None:
    """EXEC-STA-03: the sweep appends resolutions and is idempotent."""
    graph = InMemoryGraphStore()
    _legacy_flag(graph, _LEGACY, "critical", severity="critical")
    record_divergences(graph, snapshot=_snapshot(graph, "s1"), divergences=(_PFE,))

    first = resolve_legacy_flags(graph, reason="swept")
    second = resolve_legacy_flags(graph, reason="swept")

    assert first == (_LEGACY,)
    assert second == ()
    warn_key = f"flag:{subject_ref_for(_PFE)}:warn"
    assert graph.get_node("Flag", warn_key) is not None
    assert graph.get_node("FlagResolution", f"resolution:{warn_key}") is None


def test_legacy_flag_without_a_severity_prop_defaults_to_critical() -> None:
    """EXEC-STA-03: a severity-less legacy flag still joins on the default."""
    graph = InMemoryGraphStore()
    legacy = "broker-position-divergence:broker-position-snapshot:sched-2:t0"
    _legacy_flag(graph, legacy, "critical")

    assert resolve_legacy_flags(graph, reason="swept") == (legacy,)
    assert graph.get_node("FlagResolution", f"resolution:flag:{legacy}:critical")
