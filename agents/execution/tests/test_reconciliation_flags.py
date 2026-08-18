"""Divergence-flag lifecycle tests — severity follows persistence.

Agent: execution
Role: prove a first-sight divergence is `warn`, one that survives a run is
      `critical`, one that is gone is retired, and legacy flags need the sweep.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker import BrokerAccount, BrokerFill, BrokerPosition
from agents.execution.reconciliation import reconcile_run_start
from agents.execution.reconciliation_flags import (
    record_divergences,
    resolve_legacy_flags,
    subject_ref_for,
)
from agents.execution.reconciliation_store import Divergence
from agents.execution.tests.broker_protocol_helpers import NoStopBrokerMixin
from kernel import CollectingFaultSink, GraphStore, InMemoryGraphStore, Node

_ACCOUNT = BrokerAccount(
    cash_cents=10000000,
    equity_cents=10000000,
    buying_power_cents=10000000,
)
_PFE = Divergence("missing_graph_position", "PFE", "broker_qty=38")


class _MatchingBroker(NoStopBrokerMixin):
    """A broker whose holdings agree with the graph exactly."""

    def submit(self, *_args: object, **_kwargs: object) -> BrokerFill:
        raise AssertionError("reconciliation must not submit")

    def fills(self) -> tuple[BrokerFill, ...]:
        return ()

    def positions(self) -> tuple[BrokerPosition, ...]:
        return (BrokerPosition("AAPL", 2, 10000, 20000),)

    def account(self) -> BrokerAccount:
        return _ACCOUNT


def _snapshot(graph: GraphStore, key: str) -> Node:
    return graph.merge_node("BrokerPositionSnapshot", key, {"holding_count": 0})


def _unresolved(graph: GraphStore, severity: str) -> list[str]:
    resolved = {
        (n.props.get("subject_ref"), n.props.get("severity"))
        for n in graph.list_nodes("FlagResolution")
    }
    return [
        str(n.props["subject_ref"])
        for n in graph.list_nodes("Flag")
        if n.props.get("severity") == severity
        and (n.props.get("subject_ref"), severity) not in resolved
    ]


def test_first_sight_of_a_divergence_is_warn_not_critical() -> None:
    """EXEC-TRG-07: a divergence reconciliation is about to adopt is not critical."""
    graph = InMemoryGraphStore()

    record_divergences(graph, snapshot=_snapshot(graph, "s1"), divergences=(_PFE,))

    assert _unresolved(graph, "warn") == [subject_ref_for(_PFE)]
    assert _unresolved(graph, "critical") == []


def test_a_divergence_surviving_a_run_escalates_to_critical() -> None:
    """EXEC-TRG-07: adoption failed, so the flag becomes a real critical."""
    graph = InMemoryGraphStore()
    record_divergences(graph, snapshot=_snapshot(graph, "s1"), divergences=(_PFE,))

    record_divergences(graph, snapshot=_snapshot(graph, "s2"), divergences=(_PFE,))

    subject = subject_ref_for(_PFE)
    assert _unresolved(graph, "critical") == [subject]
    assert _unresolved(graph, "warn") == []
    critical = graph.get_node("Flag", f"flag:{subject}:critical")
    assert critical is not None
    assert "survived a full run" in str(critical.props["reason"])


def test_repeating_a_divergence_never_mints_a_second_unresolvable_flag() -> None:
    """EXEC-TRG-07: the run-stable subject_ref makes the dedupe guard fire."""
    graph = InMemoryGraphStore()
    for run in range(4):
        record_divergences(
            graph, snapshot=_snapshot(graph, f"s{run}"), divergences=(_PFE,)
        )

    assert len(graph.list_nodes("Flag")) == 2
    assert len(_unresolved(graph, "critical")) == 1


def test_an_adopted_divergence_is_retired_on_the_next_run() -> None:
    """EXEC-STA-03: retirement appends a FlagResolution, never mutates the Flag."""
    graph = InMemoryGraphStore()
    record_divergences(graph, snapshot=_snapshot(graph, "s1"), divergences=(_PFE,))

    record_divergences(graph, snapshot=_snapshot(graph, "s2"), divergences=())

    subject = subject_ref_for(_PFE)
    assert _unresolved(graph, "warn") == []
    resolution = graph.get_node("FlagResolution", f"resolution:flag:{subject}:warn")
    assert resolution is not None
    assert resolution.props["resolution_reason"] == "divergence no longer present"
    assert resolution.props["resolving_snapshot_key"] == "s2"
    flag = graph.get_node("Flag", f"flag:{subject}:warn")
    assert flag is not None
    assert flag.props["status"] == "pending"


def test_run_start_reconciliation_records_an_agreeing_book_without_flags() -> None:
    """EXEC-TRG-07: agreement writes the snapshot and raises nothing."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    graph.merge_node(
        "Position",
        "graph:AAPL",
        {
            "ticker": "AAPL",
            "quantity": 2,
            "opened_price_cents": 10000,
            "status": "open",
        },
    )

    snapshot = reconcile_run_start(graph, _MatchingBroker(), sink, run_id="pm-run")

    assert snapshot is not None
    assert graph.list_nodes("Flag") == ()


def test_a_flag_whose_key_contradicts_its_severity_prop_is_not_resolved() -> None:
    """EXEC-STA-03: resolution joins on the key, so a mis-keyed flag stays open."""
    graph = InMemoryGraphStore()
    legacy = "broker-position-divergence:broker-position-snapshot:sched-3:t0"
    graph.merge_node(
        "Flag",
        f"flag:{legacy}:warn",
        {"subject_ref": legacy, "severity": "critical", "status": "pending"},
    )

    assert resolve_legacy_flags(graph, reason="swept") == ()
    assert graph.list_nodes("FlagResolution") == ()
