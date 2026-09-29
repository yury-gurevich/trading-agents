"""S241 C7: barrier_scorecard counts the ledger and reports only what it can score.

Agent: forecaster
Role: prove the scorecard's counts per model, that a single settled date gives no
      interval, that an empty ledger gives three zero counts and no score, and that
      it is read-only and repeatable. The scores against EXP-018's own scorer are in
      `test_barrier_scorecard_oracle.py`.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.tests.ledger_fixture import LEDGER, card, write_ledger
from kernel import InMemoryGraphStore


def test_fewer_than_two_settled_dates_give_no_interval() -> None:
    """FORE-OUT-08: every settled claim on one as_of date: skill, but no interval."""
    graph = InMemoryGraphStore()
    write_ledger(graph, LEDGER[:3])

    scorecard = card(graph)

    assert scorecard.metrics["settled"] == 3.0
    assert "skill" in scorecard.metrics
    assert "skill_lo" not in scorecard.metrics
    assert "skill_hi" not in scorecard.metrics


def test_an_empty_ledger_reports_counts_and_no_scores() -> None:
    """FORE-OUT-08 / FORE-OUT-04: no claim at all: three zero counts, no score."""
    scorecard = card(InMemoryGraphStore())

    assert scorecard.metrics == {"settled": 0.0, "void": 0.0, "open": 0.0}
    assert scorecard.sample_size == 0
    assert scorecard.promotion_eligible is False


def test_another_models_ledger_is_its_own() -> None:
    """FORE-OUT-08: the scorecard is one model's: another model id sees nothing."""
    graph = InMemoryGraphStore()
    write_ledger(graph)

    assert card(graph, "other-model").metrics == {
        "settled": 0.0,
        "void": 0.0,
        "open": 0.0,
    }


def test_the_scorecard_is_read_only_and_repeatable() -> None:
    """FORE-IDM-05: two calls on the same ledger return the same metrics (the
    bootstrap seed is fixed) and write nothing."""
    graph = InMemoryGraphStore()
    write_ledger(graph)
    labels = ("BarrierSettlement", "BarrierForecast", "BarrierSettlementPass")
    before = {label: graph.list_nodes(label) for label in labels}

    first, second = card(graph), card(graph)

    assert first.metrics == second.metrics
    assert {label: graph.list_nodes(label) for label in labels} == before
