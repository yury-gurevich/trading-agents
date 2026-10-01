"""No graph-pull poll downloads payloads to find its work (S242 A4/A8, DL-246).

Agent: tooling
Role: run every find_pending in scope on a store that fails when the poll lists its
      own label with props or walks its processed edge per node, and pin which of
      its label's nodes it then fetches: the ones without that edge, never the rest.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from tests.poll_payload_fixtures import CASES, NOW, PayloadSpy

from agents.analyst import poll as analyst_poll
from agents.monitor import poll as monitor_poll
from agents.portfolio_manager import poll as pm_poll
from agents.provider import poll as provider_poll
from agents.provider.barrier_history import find_pending_barrier_history
from agents.reporter import poll as reporter_poll
from agents.scanner import poll as scanner_poll

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.poll_payload_fixtures import PollCase

    from kernel import GraphStore, Node

FINDERS: dict[str, Callable[[GraphStore], list[Node]]] = {
    "provider": provider_poll.find_pending,
    "scanner": scanner_poll.find_pending,
    "analyst": analyst_poll.find_pending,
    "portfolio_manager": pm_poll.find_pending,
    "monitor": monitor_poll.find_pending,
    "reporter": reporter_poll.find_pending,
    "barrier_history": lambda graph: find_pending_barrier_history(graph, now=NOW),
}


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_no_poll_downloads_a_payload_to_find_its_work(case: PollCase) -> None:
    """PROV-TRG-02 / PROV-TRG-04 / SCAN-TRG-03 / ANLZ-TRG-03 / PM-TRG-03 /
    MON-TRG-04 / RPT-TRG-04 (DL-246): a poll finds its pending work by key and edge;
    it fetches only the nodes that lack its processed edge, in list order."""
    graph = PayloadSpy()
    case.seed(graph)
    graph.arm(case.label, case.edge)

    found = FINDERS[case.name](graph)

    assert tuple(node.key for node in found) == case.pending
    assert tuple(graph.fetched) == case.candidates


def test_the_barrier_backlog_is_never_fetched() -> None:
    """PROV-TRG-04 / PROV-TRG-02 (DL-241 D11, DL-246 D2): 71 stale runs with no
    BarrierHistory and one current run: only the current run's node is ever read."""
    case = next(case for case in CASES if case.name == "barrier_history")
    graph = PayloadSpy()
    case.seed(graph)
    graph.arm(case.label, case.edge)

    found = find_pending_barrier_history(graph, now=NOW)

    assert [node.key for node in found] == ["current"]
    assert graph.fetched == ["current"]
