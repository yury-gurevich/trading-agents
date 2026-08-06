"""Shadow-book pricing, horizon, and disposition tests.

Agent: orchestration
Role: prove recommendation outcomes are reconstructed from immutable graph facts.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest

from kernel import InMemoryGraphStore
from orchestration.shadow_book import derive_shadow_book
from orchestration.tests.shadow_book_helpers import (
    add_market,
    bar,
    recommendation,
    seed_run,
)

AS_OF = date(2026, 8, 3)
NEXT_DAY = date(2026, 8, 4)


def test_a1_reference_price_comes_from_the_run_snapshot() -> None:
    """S160-A1: a later snapshot cannot silently re-price the recommendation."""
    graph = InMemoryGraphStore()
    seed_run(
        graph,
        "analyst-a1",
        AS_OF,
        (recommendation("MSFT"),),
        (bar("MSFT", AS_OF, 100.0),),
    )
    add_market(
        graph,
        "market-later",
        NEXT_DAY,
        (bar("MSFT", AS_OF, 999.0), bar("MSFT", NEXT_DAY, 110.0)),
    )

    (outcome,) = derive_shadow_book(graph, (1,))

    assert outcome.reference_price == 100.0
    assert outcome.forward_price == 110.0
    assert outcome.forward_return == pytest.approx(0.10)


def test_a2_missing_ticker_is_reported_unpriceable() -> None:
    """S160-A2: a missing run-local ticker remains visible, never dropped."""
    graph = InMemoryGraphStore()
    seed_run(
        graph,
        "analyst-a2",
        AS_OF,
        (recommendation("MSFT"),),
        (bar("AAPL", AS_OF, 50.0),),
    )
    add_market(graph, "market-future", NEXT_DAY, (bar("AAPL", NEXT_DAY, 55.0),))

    (outcome,) = derive_shadow_book(graph, (1,))

    assert outcome.status == "unpriceable"
    assert outcome.reference_price is None
    assert outcome.ticker == "MSFT"


def test_a3_reference_price_respects_the_as_of_boundary() -> None:
    """S160-A3: a planted later bar in the run snapshot is never the reference."""
    graph = InMemoryGraphStore()
    bars = (bar("MSFT", AS_OF, 100.0), bar("MSFT", NEXT_DAY, 777.0))
    seed_run(graph, "analyst-a3", AS_OF, (recommendation("MSFT"),), bars)

    (outcome,) = derive_shadow_book(graph, (1,))

    assert outcome.reference_price == 100.0
    assert outcome.forward_price == 777.0


def test_b2_unelapsed_horizon_is_excluded_not_imputed() -> None:
    """S160-B2: a planted 20-day horizon has no zero-filled return."""
    graph = InMemoryGraphStore()
    seed_run(
        graph,
        "analyst-b2",
        AS_OF,
        (recommendation("MSFT"),),
        (bar("MSFT", AS_OF, 100.0),),
    )
    add_market(graph, "market-next", NEXT_DAY, (bar("MSFT", NEXT_DAY, 110.0),))

    (outcome,) = derive_shadow_book(graph, (20,))

    assert outcome.status == "not_yet_elapsed"
    assert outcome.forward_price is None
    assert outcome.forward_return is None


def test_forward_price_missing_on_elapsed_date_is_unpriceable() -> None:
    """An elapsed horizon with a planted ticker gap is not called unelapsed."""
    graph = InMemoryGraphStore()
    seed_run(
        graph,
        "analyst-gap",
        AS_OF,
        (recommendation("MSFT"),),
        (bar("MSFT", AS_OF, 100.0),),
    )
    add_market(graph, "market-next", NEXT_DAY, (bar("AAPL", NEXT_DAY, 50.0),))

    (outcome,) = derive_shadow_book(graph, (1,))

    assert outcome.status == "unpriceable"
    assert outcome.reference_price == 100.0
    assert outcome.forward_return is None


@pytest.mark.parametrize("horizons", [(), (0,)])
def test_horizons_must_be_positive(horizons: tuple[int, ...]) -> None:
    """A planted empty or non-positive horizon configuration is rejected."""
    with pytest.raises(ValueError, match="positive trading-day"):
        derive_shadow_book(InMemoryGraphStore(), horizons)


def test_missing_lineage_is_unpriceable_and_incomplete_runs_are_skipped() -> None:
    """Missing planted source facts stay explicit without hiding valid runs."""
    graph = InMemoryGraphStore()
    seed_run(
        graph,
        "analyst-no-scan",
        AS_OF,
        (recommendation("MSFT"),),
        (),
        create_scan=False,
        include_pm=False,
    )
    seed_run(
        graph,
        "analyst-no-edge",
        AS_OF,
        (recommendation("AAPL"),),
        (),
        link_market=False,
        include_pm=False,
    )
    graph.merge_node("AnalystRun", "incomplete", {"created_at": AS_OF.isoformat()})
    graph.merge_node("PMRun", "unlinked", {"order_intent_set": {}})

    outcomes = derive_shadow_book(graph, (1,))

    assert [(item.ticker, item.status) for item in outcomes] == [
        ("AAPL", "unpriceable"),
        ("MSFT", "unpriceable"),
    ]


@pytest.mark.parametrize(
    ("key", "message"),
    [
        ("malformed", "malformed Recommendation key"),
        ("missing-run:MSFT", "has no matching AnalystRun"),
    ],
)
def test_every_recommendation_must_join_to_an_analyst_run(
    key: str, message: str
) -> None:
    """A planted malformed or orphan recommendation fails loudly, never disappears."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Recommendation",
        key,
        {
            "ticker": "MSFT",
            "action": "buy",
            "confidence": 0.62,
            "technical_score": 0.75,
        },
    )

    with pytest.raises(ValueError, match=message):
        derive_shadow_book(graph, (1,))
