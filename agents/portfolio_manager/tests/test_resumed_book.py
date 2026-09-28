"""S240 a resumed PM weighs its book at the snapshot of the run it resumes.

Agent: portfolio_manager
Role: prove the bounded resume-lineage walk behind the PM's snapshot choice.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.portfolio_manager.graph_portfolio import portfolio_from_graph
from agents.portfolio_manager.run_snapshot import MAX_RESUME_HOPS
from agents.portfolio_manager.tests.book_helpers import (
    CountingGraph,
    book_snapshot,
    held,
    resumed_request,
)
from kernel import InMemoryGraphStore

_SOURCE = "sched-2026-09-25"
_CHILD = f"{_SOURCE}-resume-pm"
_SEED = Decimal("100000")


def _source_book(graph: InMemoryGraphStore) -> None:
    held(graph, "held:INTC", "INTC", 10, cost_cents=9_000, adoption_cents=100_000)
    book_snapshot(graph, _SOURCE, {"INTC": 150_000}, equity_cents=5_000_000)


def test_a_resumed_pm_reads_the_snapshot_of_the_run_it_resumes() -> None:
    """PM-IN-05 / PM-IDN-01: a child with no snapshot reads its source's, not seed."""
    graph = InMemoryGraphStore()
    _source_book(graph)
    resumed_request(graph, _CHILD, _SOURCE)

    portfolio = portfolio_from_graph(graph, _SEED, run_id=_CHILD)

    assert portfolio.cash.amount == Decimal("50000")
    assert portfolio.account_equity_cents == 5_000_000
    assert portfolio.position_values["INTC"].amount == Decimal("1500")


def test_a_resumed_run_with_its_own_snapshot_reads_its_own() -> None:
    """PM-IN-05: the run's own snapshot wins; the lineage is read only without one."""
    graph = InMemoryGraphStore()
    _source_book(graph)
    resumed_request(graph, _CHILD, _SOURCE)
    book_snapshot(graph, _CHILD, {"INTC": 170_000}, equity_cents=6_000_000)

    portfolio = portfolio_from_graph(graph, _SEED, run_id=_CHILD)

    assert portfolio.account_equity_cents == 6_000_000
    assert portfolio.position_values["INTC"].amount == Decimal("1700")


def test_a_resume_of_a_resume_reads_the_first_ancestor_with_a_snapshot() -> None:
    """PM-IN-05: a resume of a resume chains to the first ancestor with a snapshot."""
    graph = InMemoryGraphStore()
    _source_book(graph)
    resumed_request(graph, _CHILD, _SOURCE)
    grandchild = f"{_CHILD}-resume-pm"
    resumed_request(graph, grandchild, _CHILD)

    portfolio = portfolio_from_graph(graph, _SEED, run_id=grandchild)

    assert portfolio.account_equity_cents == 5_000_000
    assert portfolio.position_values["INTC"].amount == Decimal("1500")


def test_a_broken_lineage_seeds_from_starting_cash() -> None:
    """PM-IN-05 / PM-STA-01: a broken lineage seeds; no other run's snapshot is read."""
    graph = InMemoryGraphStore()
    held(graph, "held:INTC", "INTC", 10, cost_cents=9_000, adoption_cents=100_000)
    resumed_request(graph, _CHILD, "sched-1999-01-01")
    book_snapshot(graph, "sched-2026-09-24", {"INTC": 170_000}, equity_cents=7_000_000)
    graph.merge_node("RunRequest", "run-request:orphan", {"run_id": "orphan"})

    for run_id in (_CHILD, "orphan", "never-placed"):
        portfolio = portfolio_from_graph(graph, _SEED, run_id=run_id)
        assert portfolio.cash.amount == _SEED
        assert portfolio.account_equity_cents is None
        assert portfolio.position_values["INTC"].amount == Decimal("1000")


def test_a_looping_lineage_stops_at_the_bound_without_raising() -> None:
    """PM-IN-05: a lineage that loops ends at the hop bound, seeded, never raising."""
    graph = CountingGraph(limit=10 * (MAX_RESUME_HOPS + 1))
    resumed_request(graph, "loop-a", "loop-b")
    resumed_request(graph, "loop-b", "loop-a")
    graph.reads = 0

    portfolio = portfolio_from_graph(graph, _SEED, run_id="loop-a")

    assert portfolio.cash.amount == _SEED
    assert graph.reads <= MAX_RESUME_HOPS + 1


def test_an_unscoped_evaluation_weighs_at_the_latest_snapshot() -> None:
    """PM-IN-05: with no run id, the latest snapshot's marks, once per ticker."""
    graph = InMemoryGraphStore()
    _source_book(graph)
    held(graph, "held:INTC:b", "INTC", 5, cost_cents=9_000, adoption_cents=50_000)
    graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot:later",
        {
            "run_id": "later",
            "created_at": "2026-09-26T13:25:00+00:00",
            "holdings": [{"ticker": "INTC", "market_value_cents": 180_000}],
        },
    )

    portfolio = portfolio_from_graph(graph, _SEED)

    assert portfolio.position_values["INTC"].amount == Decimal("1800")
