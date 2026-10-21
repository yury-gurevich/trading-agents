"""The held book joins only the run session's keyed, readable held claims.

Agent: orchestration
Role: prove A1-A5 against literal lots, claims and independent read counters.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import get_args

from kernel import InMemoryGraphStore
from orchestration.tests.book_fixtures import DAY, CountingGraph, claim, lot


def test_the_book_joins_each_held_name_to_its_sessions_claim() -> None:
    """DSP-OUT-10: sum both lots and round the session's held claim to cents."""
    from orchestration.book_odds import HeldClaim, HeldName, book_odds

    graph = InMemoryGraphStore()
    lot(graph, "COP", 8, 12441, key="cop-a")
    lot(graph, "COP", 2, 13000, key="cop-b")
    claim(
        graph,
        "COP",
        prices=(145.95, 117.08, 130.5765),
        basis="rebased",
        probabilities=(0.002, 0.395, 0.603),
    )
    claim(graph, "COP", day=date(2026, 10, 17), prices=(90.0, 80.0, 100.0))
    claim(graph, "COP", key="barrier-garch-v1:COP:2026-10-20")

    odds = book_odds(graph, DAY)

    assert odds is not None
    assert odds.as_of == DAY
    assert odds.names == (
        HeldName(
            "COP",
            10,
            125528,
            HeldClaim(14595, 11708, 13058, True, 0.002, 0.395, 0.603, 10),
        ),
    )
    assert odds.unforecast == ()


def test_a_name_without_a_readable_claim_is_unforecast() -> None:
    """DSP-OUT-10: bool prices, absent claims and empty nodes are unforecast."""
    from orchestration.book_odds import book_odds

    graph = InMemoryGraphStore()
    for ticker in ("DOW", "MO", "PFE", "XOM"):
        lot(graph, ticker, 1, 10000)
    claim(graph, "DOW", stop_price=True)
    claim(graph, "PFE")
    graph.merge_node("BarrierForecast", "barrier-garch-v1:held:XOM:2026-10-20", {})

    odds = book_odds(graph, DAY)

    assert odds is not None
    assert odds.unforecast == ("DOW", "MO", "XOM")
    assert tuple(name.ticker for name, _ in odds.forecast) == ("PFE",)


def test_nothing_held_is_no_book() -> None:
    """DSP-OUT-10: closed, absent and superseded lots never enter the book."""
    from orchestration.book_odds import book_odds

    graph = InMemoryGraphStore()
    lot(graph, "COP", 8, 12441, status="closed")
    lot(graph, "MO", 5, 6500, broker_absent=True)
    lot(graph, "KO", 10, 8692, broker_superseded_by="replacement")
    claim(graph, "COP")

    assert book_odds(graph, DAY) is None


def test_the_book_reads_positions_once_and_each_claim_by_key() -> None:
    """DSP-OUT-10: one Position listing and four keyed claim reads, no listing."""
    from orchestration.book_odds import book_odds

    graph = CountingGraph()
    for ticker in ("COP", "MO", "KO", "GOOG"):
        lot(graph, ticker, 1, 10000)
        claim(graph, ticker)
    graph.listings.clear()
    graph.keyed.clear()

    odds = book_odds(graph, DAY)

    assert odds is not None
    assert len(odds.forecast) == 4
    assert graph.listings == {"Position": 1}
    assert graph.keyed == {"BarrierForecast": 4}


def test_the_label_and_prefix_are_the_forecasters() -> None:
    """DSP-OUT-10: the dispatcher's independent vocabulary matches its owner."""
    from agents.forecaster.barrier_store import BARRIER_LABEL, HELD_KEY_SEGMENT
    from agents.forecaster.domain.barrier_garch import BARRIER_MODEL_ID
    from agents.forecaster.held_claim import TargetBasis
    from orchestration import book_odds

    assert book_odds.BARRIER_LABEL == BARRIER_LABEL
    assert f"{BARRIER_MODEL_ID}:{HELD_KEY_SEGMENT}:" == book_odds.HELD_CLAIM_PREFIX
    assert book_odds.PASSED_BASIS in get_args(TargetBasis)
