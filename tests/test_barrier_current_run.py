"""S239 D11: the deployed loops claim only a current AnalystRun, never the backlog.

Agent: tooling
Role: prove the one shared rule (contracts/barrier_history.is_current_run) and that
      the provider's and the forecaster's deployed finders both apply it, while the
      unguarded finders the local pipeline uses are unchanged.
External I/O: none (in-memory graph, injected clock).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.forecaster.poll import find_pending as forecaster_pending
from agents.provider.barrier_history import find_pending_barrier_history
from agents.provider.poll import find_current_work
from agents.provider.tests.barrier_history_helpers import analyst_run, rec
from contracts.barrier_history import (
    CLAIM_RUN_MAX_AGE,
    barrier_history_key,
    is_current_run,
)
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import Node

NOW = datetime(2026, 9, 29, 23, 0, tzinfo=UTC)


def _run(graph: InMemoryGraphStore, key: str, created_at: str | None) -> Node:
    node = analyst_run(graph, rec("AAPL", "buy"), key=key)
    if created_at is None:
        return node
    return graph.merge_node("AnalystRun", key, {"created_at": created_at})


def _graph() -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    _run(graph, "fresh", (NOW - timedelta(hours=1)).isoformat())
    _run(graph, "old", (NOW - timedelta(days=2)).isoformat())
    _run(graph, "undated", None)
    return graph


def _keys(nodes: list[Node]) -> set[str]:
    return {node.key for node in nodes}


def test_the_rule_is_fail_closed() -> None:
    """PROV-TRG-04 / FORE-TRG-01 (DL-241 D11): current within 24 h; no date, a bad
    date or a zone-less date is not current."""
    edge = NOW - CLAIM_RUN_MAX_AGE
    assert is_current_run({"created_at": edge.isoformat()}, NOW)
    just_old = (edge - timedelta(seconds=1)).isoformat()
    assert not is_current_run({"created_at": just_old}, NOW)
    assert not is_current_run({}, NOW)
    assert not is_current_run({"created_at": "yesterday"}, NOW)
    assert not is_current_run({"created_at": "2026-09-29T22:00:00"}, NOW)
    assert not is_current_run({"created_at": 1}, NOW)


def test_the_provider_writes_history_for_a_current_run_only() -> None:
    """PROV-TRG-04 (DL-241 D11): the backlog of old runs is never fetched."""
    graph = _graph()

    assert _keys(find_pending_barrier_history(graph, now=NOW)) == {"fresh"}
    assert _keys(find_pending_barrier_history(graph)) == {"fresh", "old", "undated"}


def test_the_provider_deployed_work_list_uses_the_wall_clock() -> None:
    """PROV-TRG-04 (DL-241 D11): the loop the container runs is the guarded one."""
    graph = InMemoryGraphStore()
    _run(graph, "now", datetime.now(tz=UTC).isoformat())
    _run(graph, "old", (datetime.now(tz=UTC) - timedelta(days=2)).isoformat())

    items = find_current_work(graph)

    found = [(item.kind, item.node.key) for item in items]
    assert found == [("barrier_history", "now")]


def test_the_forecaster_claims_a_current_run_only() -> None:
    """FORE-TRG-01 (DL-241 D11): an old run is never claimed on later bars."""
    graph = _graph()
    for key in ("fresh", "old", "undated"):
        graph.merge_node("BarrierHistory", barrier_history_key(key), {})

    assert _keys(forecaster_pending(graph, now=NOW)) == {"fresh"}
    assert _keys(forecaster_pending(graph)) == {"fresh", "old", "undated"}
