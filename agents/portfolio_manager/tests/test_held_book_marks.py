"""S240 the PM weighs its held book at the run's own snapshot marks.

Agent: portfolio_manager
Role: prove held values come from the run's snapshot, once per ticker, with fallbacks.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.graph_portfolio import portfolio_from_graph
from agents.portfolio_manager.tests.book_helpers import book_snapshot, held
from agents.portfolio_manager.tests.s184_helpers import buy
from contracts.common import Money
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from contracts.portfolio_manager import OrderIntent, RejectedOrder

_RUN = "sched-2026-09-25"


def _amounts(graph: InMemoryGraphStore, run_id: str | None) -> dict[str, Decimal]:
    portfolio = portfolio_from_graph(graph, Decimal("100000"), run_id=run_id)
    return {ticker: money.amount for ticker, money in portfolio.position_values.items()}


def test_a_held_name_is_weighed_at_the_runs_snapshot_mark() -> None:
    """PM-IN-05 / PM-IDN-01: the run's snapshot mark wins over the adoption mark."""
    graph = InMemoryGraphStore()
    held(graph, "held:INTC", "INTC", 10, cost_cents=9_000, adoption_cents=100_000)
    book_snapshot(graph, _RUN, {"INTC": 150_000})

    assert _amounts(graph, _RUN) == {"INTC": Decimal("1500")}


def test_a_ticker_held_by_two_nodes_is_weighed_once() -> None:
    """PM-IN-05: one value per ticker, however many active Position nodes hold it."""
    graph = InMemoryGraphStore()
    held(graph, "held:AAPL:a", "AAPL", 10, cost_cents=5_000, adoption_cents=50_000)
    held(graph, "held:AAPL:b", "AAPL", 10, cost_cents=5_000, adoption_cents=50_000)
    book_snapshot(graph, _RUN, {"AAPL": 150_000})

    assert _amounts(graph, _RUN) == {"AAPL": Decimal("1500")}


def test_the_fallbacks_are_the_adoption_mark_then_the_cost_basis() -> None:
    """PM-IN-05 / PM-STA-01: unlisted -> adoption mark -> cost; no snapshot -> seed."""
    graph = InMemoryGraphStore()
    held(graph, "held:XOM", "XOM", 5, cost_cents=10_000, adoption_cents=40_000)
    held(graph, "held:MSFT", "MSFT", 1, cost_cents=30_000, adoption_cents=20_000)
    held(graph, "held:KO", "KO", 3, cost_cents=5_000)
    book_snapshot(graph, _RUN, {"XOM": 60_000, "NOTHELD": 99_900})

    assert _amounts(graph, _RUN) == {
        "XOM": Decimal("600"),
        "MSFT": Decimal("200"),
        "KO": Decimal("150"),
    }
    seeded = portfolio_from_graph(graph, Decimal("12345"), run_id="no-snapshot")
    assert seeded.cash.amount == Decimal("12345")
    assert seeded.account_equity_cents is None
    assert {k: v.amount for k, v in seeded.position_values.items()} == {
        "XOM": Decimal("400"),
        "MSFT": Decimal("200"),
        "KO": Decimal("150"),
    }


def test_a_stale_snapshot_still_lends_the_marks_it_read() -> None:
    """PM-IN-05 / PM-NEV-04: listed marks are used; the account stays unavailable."""
    graph = InMemoryGraphStore()
    held(graph, "held:INTC", "INTC", 10, cost_cents=9_000, adoption_cents=100_000)
    held(graph, "held:KO", "KO", 3, cost_cents=5_000, adoption_cents=16_000)
    book_snapshot(graph, _RUN, {"INTC": 150_000}, status="stale")

    portfolio = portfolio_from_graph(graph, Decimal("100000"), run_id=_RUN)

    assert portfolio.account_status == "stale"
    assert portfolio.cash.amount == Decimal("0")
    assert {k: v.amount for k, v in portfolio.position_values.items()} == {
        "INTC": Decimal("1500"),
        "KO": Decimal("160"),
    }


def test_the_sector_cap_decides_on_the_snapshot_mark() -> None:
    """PM-NEV-06 / PM-IN-05: a held winner's snapshot mark fills the sector cap."""
    graph = InMemoryGraphStore()
    held(graph, "held:JPM", "JPM", 20, cost_cents=10_000, adoption_cents=200_000)
    held(
        graph, "held:OTHER", "OTHER", 1, cost_cents=1_400_000, adoption_cents=1_400_000
    )
    book_snapshot(graph, "adoption-only", {"OTHER": 1_400_000})
    book_snapshot(graph, _RUN, {"JPM": 600_000, "OTHER": 1_400_000})

    adoption = _evaluate(graph, "adoption-only")
    current = _evaluate(graph, _RUN)

    assert [intent.ticker for intent in adoption[0]] == ["WFC"]
    assert current[0] == ()
    assert [(item.ticker, item.reason) for item in current[1]] == [
        ("WFC", "sector_concentration")
    ]


def _evaluate(
    graph: InMemoryGraphStore, run_id: str
) -> tuple[tuple[OrderIntent, ...], tuple[RejectedOrder, ...]]:
    return evaluate_recommendations(
        (buy("WFC"),),
        {"WFC": Money(amount=Decimal("986.86"))},
        portfolio_from_graph(graph, Decimal("100000"), run_id=run_id),
        max_position_pct=Decimal("0.01"),
        max_positions=60,
        cash_buffer_pct=Decimal("0.05"),
        min_order_quantity=1,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        min_reward_risk_ratio=1.5,
        sectors={"JPM": "Banking", "OTHER": "Other", "WFC": "Banking"},
        max_sector_pct=Decimal("0.30"),
        max_names_per_sector=3,
    )
