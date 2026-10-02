"""S252 A3: both forecaster finders exclude the stale backlog before fetching props.

Agent: forecaster
Role: prove deployed recency bounds and unbounded local-pipeline discovery.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from tests.poll_payload_remaining import seed_forecaster_backlog
from tests.poll_payload_support import NOW, PayloadSpy

from agents.forecaster.poll import find_pending
from agents.forecaster.settlement_pass import find_pending_settlement
from contracts.barrier_history import CLAIM_RUN_MAX_AGE

if TYPE_CHECKING:
    from collections.abc import Callable

    from kernel import Node


@pytest.mark.parametrize(
    ("finder", "edge"),
    [(find_pending, "FORECAST_BY"), (find_pending_settlement, "BARRIER_SETTLEMENT_BY")],
)
@pytest.mark.parametrize("deployed", [True, False], ids=["deployed", "local"])
def test_each_forecaster_finder_fetches_only_its_current_backlog(
    finder: Callable[..., list[Node]], edge: str, deployed: bool
) -> None:
    """FORE-TRG-01 / FORE-IDM-05: deployed fetches one current run; local all 72
    in order.
    """
    graph = PayloadSpy()
    seed_forecaster_backlog(graph)
    graph.arm("AnalystRun", edge)
    expected = (
        ["current"] if deployed else [*(f"stale-{i:02d}" for i in range(71)), "current"]
    )

    found = finder(graph, now=NOW if deployed else None)

    assert graph.fetched == expected
    assert [node.key for node in found] == expected


@pytest.mark.parametrize(
    "finder", [find_pending, find_pending_settlement], ids=["forecast", "settlement"]
)
def test_both_finders_keep_the_shared_current_run_predicate(
    finder: Callable[..., list[Node]],
) -> None:
    """FORE-TRG-01: missing/non-string stamps are not fetched; over-included bad
    strings fail closed.
    """
    graph = PayloadSpy()
    for key, props in (
        ("missing", {}),
        ("number", {"created_at": 123}),
        ("garbage", {"created_at": "unreadable"}),
        ("naive", {"created_at": NOW.replace(tzinfo=None).isoformat()}),
        ("boundary", {"created_at": (NOW - CLAIM_RUN_MAX_AGE).isoformat()}),
    ):
        graph.merge_node("AnalystRun", key, props)
    edge = "FORECAST_BY" if finder is find_pending else "BARRIER_SETTLEMENT_BY"
    graph.arm("AnalystRun", edge)

    found = finder(graph, now=NOW)

    assert graph.fetched == ["garbage", "naive", "boundary"]
    assert [node.key for node in found] == ["boundary"]
