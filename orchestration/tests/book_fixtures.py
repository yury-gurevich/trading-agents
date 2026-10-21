"""Synthetic held lots and claims for the book's brief and dashboard proofs.

Agent: orchestration
Role: plant the fixed book examples and count graph reads independently.
External I/O: none; every graph is in memory.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import GraphStore, Node

DAY = date(2026, 10, 20)
BOOK_LINES = (
    "Book: 4 held · 2 past their target: +$243.44 now "
    "(+$145.68 above target), \u2212$88.64 at their stops",
    "Odds, next 10 sessions, 4 names (not yet scored): "
    "target first 1.0 · stop first 0.4 · neither 2.5 · likelier to stop: GOOG 43 %",
)


def lot(
    graph: GraphStore,
    ticker: str,
    quantity: int,
    price: int,
    *,
    key: str | None = None,
    **props: object,
) -> Node:
    """Plant one lot, with explicit inactive markers when a case needs them."""
    return graph.merge_node(
        "Position",
        key or f"lot:{ticker}",
        {
            "ticker": ticker,
            "quantity": quantity,
            "opened_price_cents": price,
            "status": "open",
        }
        | props,
    )


def claim(
    graph: GraphStore,
    ticker: str,
    *,
    day: date = DAY,
    prices: tuple[float, float, float] = (100.0, 95.0, 110.0),
    basis: str = "declared",
    probabilities: tuple[float, float, float] = (0.1, 0.5, 0.4),
    key: str | None = None,
    **props: object,
) -> Node:
    """Plant a literal held key, never deriving it from the reader under test."""
    close, stop, target = prices
    p_stop, p_target, p_neither = probabilities
    return graph.merge_node(
        "BarrierForecast",
        key or f"barrier-garch-v1:held:{ticker}:{day.isoformat()}",
        {
            "ticker": ticker,
            "as_of": day.isoformat(),
            "entry_close": close,
            "stop_price": stop,
            "target_price": target,
            "target_basis": basis,
            "p_stop_first": p_stop,
            "p_target_first": p_target,
            "p_neither": p_neither,
            "horizon_sessions": 10,
        }
        | props,
    )


def seed_book(graph: GraphStore, day: date = DAY) -> None:
    """A6's four names, five lots and fixed session claims."""
    for ticker, quantity, price, key in (
        ("COP", 8, 12441, "cop"),
        ("MO", 5, 6500, "mo-a"),
        ("MO", 3, 6700, "mo-b"),
        ("KO", 10, 8692, "ko"),
        ("GOOG", 3, 34170, "goog"),
    ):
        lot(graph, ticker, quantity, price, key=key)
    for ticker, prices, basis, probabilities in (
        ("COP", (145.95, 117.08, 130.58), "rebased", (0.002, 0.395, 0.603)),
        ("MO", (74.64, 62.00, 71.80), "rebased", (0.002, 0.030, 0.968)),
        ("KO", (93.49, 82.57, 95.612), "declared", (0.001, 0.550, 0.449)),
        ("GOOG", (336.40, 324.61, 375.87), "declared", (0.430, 0.071, 0.499)),
    ):
        claim(
            graph,
            ticker,
            day=day,
            prices=prices,
            basis=basis,
            probabilities=probabilities,
        )


class CountingGraph(InMemoryGraphStore):
    """Count each read API by label, without changing its semantics."""

    def __init__(self) -> None:
        super().__init__()
        self.listings: Counter[str] = Counter()
        self.keyed: Counter[str] = Counter()

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        self.listings[label] += 1
        return super().list_nodes(label)

    def get_node(self, label: str, key: str) -> Node | None:
        self.keyed[label] += 1
        return super().get_node(label, key)
