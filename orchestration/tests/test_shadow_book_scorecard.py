"""Shadow-book read-only and scorecard tests.

Agent: orchestration
Role: prove complete-case statistics, explicit counts, and zero graph writes.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest

from kernel import InMemoryGraphStore
from orchestration.shadow_book import derive_shadow_book
from orchestration.shadow_book_scorecard import render_scorecard, score_rows
from orchestration.shadow_book_settings import ShadowBookSettings
from orchestration.tests.shadow_book_helpers import (
    add_market,
    bar,
    graph_census,
    recommendation,
    seed_run,
)

AS_OF = date(2026, 8, 3)
NEXT_DAY = date(2026, 8, 4)


def test_b4_full_derivation_preserves_every_node_and_edge_count() -> None:
    """S160-B4: every per-label node and edge count is identical after derivation."""
    graph = _scorecard_graph()
    graph.merge_node("UnrelatedFact", "untouched", {"value": 1})
    before = graph_census(graph)

    outcomes = derive_shadow_book(graph, (1, 5, 20))
    render_scorecard(outcomes, (1, 5, 20), confidence_bucket_width=0.05)

    assert graph_census(graph) == before


def test_d1_repeated_derivation_is_identical_and_write_free() -> None:
    """S160-D1: a second read-only pass returns the same rows and writes nothing."""
    graph = _scorecard_graph()
    before = graph_census(graph)

    first = derive_shadow_book(graph, (1,))
    second = derive_shadow_book(graph, (1,))

    assert second == first
    assert graph_census(graph) == before


def test_d2_scorecard_reports_n_and_unpriceable() -> None:
    """S160-D2: a planted missing price appears in coverage and sample counts."""
    graph = _scorecard_graph(include_unpriceable=True)
    outcomes = derive_shadow_book(graph, (1,))

    report = render_scorecard(outcomes, (1,), confidence_bucket_width=0.05)

    assert "recommendations_seen=3" in report
    assert "reference_unpriceable=1" in report
    assert (
        "dispositions taken=1 blocked_capacity=1 blocked_other=1 not_actionable=0"
        in report
    )
    assert "coverage n=3 scored=2 unpriceable=1 not_yet_elapsed=0" in report
    assert "| disposition | blocked_capacity | 1 |" in report


def test_d3_taken_and_capacity_buckets_keep_their_own_means() -> None:
    """S160-D3: planted opposite returns cannot collapse into one disposition mean."""
    outcomes = derive_shadow_book(_scorecard_graph(), (1,))
    rows = {
        row.bucket: row
        for row in score_rows(outcomes, confidence_bucket_width=0.05)
        if row.cut == "disposition"
    }

    assert rows["taken"].n == 1
    assert rows["taken"].mean_return == pytest.approx(0.10)
    assert rows["blocked_capacity"].n == 1
    assert rows["blocked_capacity"].mean_return == pytest.approx(-0.10)


def test_empty_complete_cases_render_n_zero_instead_of_statistics() -> None:
    """A planted unelapsed horizon renders exclusion rather than a zero return."""
    graph = _scorecard_graph()
    outcomes = derive_shadow_book(graph, (20,))

    report = render_scorecard(outcomes, (20,), confidence_bucket_width=0.05)

    assert "not_yet_elapsed=2" in report
    assert "| all | no complete outcomes | 0 | N/A | N/A | N/A |" in report


def test_shadow_book_horizons_are_justified_sorted_tunables() -> None:
    """Configured horizons are deterministic and duplicate overrides collapse."""
    defaults = ShadowBookSettings(_env_file=None)
    overridden = ShadowBookSettings(
        _env_file=None,
        short_horizon_days=5,
        medium_horizon_days=1,
        long_horizon_days=5,
    )
    assert defaults.horizons == (1, 5, 20)
    assert overridden.horizons == (1, 5)
    assert defaults.confidence_bucket_width == 0.05


@pytest.mark.parametrize("width", [0.0, 1.1])
def test_confidence_bucket_width_must_be_bounded(width: float) -> None:
    """A planted invalid confidence width is rejected before statistics."""
    outcomes = derive_shadow_book(_scorecard_graph(), (1,))
    with pytest.raises(ValueError, match="bucket width"):
        score_rows(outcomes, confidence_bucket_width=width)


def _scorecard_graph(*, include_unpriceable: bool = False) -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    seed_run(
        graph,
        "analyst-taken",
        AS_OF,
        (recommendation("AAPL", confidence=0.62),),
        (bar("AAPL", AS_OF, 100.0),),
        approved=("AAPL",),
    )
    seed_run(
        graph,
        "analyst-blocked",
        AS_OF,
        (recommendation("MSFT", confidence=0.55),),
        (bar("MSFT", AS_OF, 100.0),),
        rejected=(("MSFT", "max_positions"),),
    )
    if include_unpriceable:
        seed_run(
            graph,
            "analyst-missing",
            AS_OF,
            (recommendation("NVDA", action="hold", confidence=0.50),),
            (bar("SPY", AS_OF, 500.0),),
            rejected=(("NVDA", "hold_recommendation"),),
        )
    add_market(
        graph,
        "market-forward",
        NEXT_DAY,
        (bar("AAPL", NEXT_DAY, 110.0), bar("MSFT", NEXT_DAY, 90.0)),
    )
    return graph
