"""Every poll finds the same work, in the same order, as before S242 (A5, DL-246).

Agent: tooling
Role: run each key-and-edge finder and its pre-fix list-then-walk oracle on the same
      fixture, on the in-memory store and on the Postgres adapter over its fake.
External I/O: none (in-memory graph and fake psycopg connection).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from tests.graph_postgres_keys_fake import keys_store
from tests.poll_payload_fixtures import CASES, NOW
from tests.test_poll_payloads import FINDERS

from kernel import InMemoryGraphStore
from tests import poll_reference

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.poll_payload_fixtures import PollCase

    from kernel import GraphStore, Node

ORACLES: dict[str, Callable[[GraphStore], list[Node]]] = {
    "provider": poll_reference.simple("RunRequest", "INGESTED_BY"),
    "scanner": poll_reference.simple("MarketData", "SCANNED_BY"),
    "analyst": poll_reference.analyst,
    "portfolio_manager": poll_reference.simple("AnalystRun", "EVALUATED_BY"),
    "monitor": poll_reference.simple("ExecutionRun", "MONITORED_BY"),
    "reporter": poll_reference.reporter,
    "barrier_history": lambda graph: poll_reference.barrier(graph, NOW),
}


def _keys(nodes: list[Node]) -> list[str]:
    return [node.key for node in nodes]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_the_memory_store_finds_the_old_pending_set_in_order(case: PollCase) -> None:
    """PROV-TRG-02 / PROV-TRG-04 / SCAN-IDM-02 / ANLZ-IDM-02 / PM-IDM-02 /
    MON-ORD-01 / RPT-TRG-04 (DL-246 D3): same nodes, same order, same props."""
    graph = InMemoryGraphStore()
    case.seed(graph)

    found = FINDERS[case.name](graph)

    assert found == ORACLES[case.name](graph)
    assert _keys(found) == list(case.pending)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_the_postgres_store_finds_the_old_pending_set_in_order(
    case: PollCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PROV-TRG-02 / PROV-TRG-04 / MON-ORD-01 (DL-246 D3): on the Postgres
    adapter the order is list_nodes' key order, and the set is the oracle's."""
    graph, _fake = keys_store(monkeypatch)
    case.seed(graph)

    found = FINDERS[case.name](graph)

    assert found == ORACLES[case.name](graph)
    assert _keys(found) == sorted(case.pending)
