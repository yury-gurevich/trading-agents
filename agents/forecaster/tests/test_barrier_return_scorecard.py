"""Sprint 288 A10-A12: return scores join the existing ledger additively.

Agent: forecaster
Role: pin literal score values, historical names and separate held cohorts.
External I/O: none.
"""

import pytest

from agents.forecaster.tests.ledger_fixture import card, write_ledger
from agents.forecaster.tests.s288_return_fixtures import (
    RETURN_SCORES,
    write_return_case,
    write_return_ledger,
)
from kernel import InMemoryGraphStore


def test_the_return_scores_appear_once_a_claim_that_stated_one_settles() -> None:
    """FORE-OUT-12 / FORE-OUT-08: S241 keeps 14 names; new returns have exact scores."""
    historical = InMemoryGraphStore()
    write_ledger(historical)
    assert set(card(historical).metrics) == {
        "settled",
        "void",
        "open",
        "realised_stop",
        "realised_target",
        "realised_neither",
        "declared_stop",
        "declared_target",
        "declared_neither",
        "brier_model",
        "brier_climatology",
        "skill",
        "skill_lo",
        "skill_hi",
    }
    graph = InMemoryGraphStore()
    write_return_ledger(graph)

    metrics = card(graph).metrics

    assert {name: metrics[name] for name in RETURN_SCORES} == pytest.approx(
        {
            "return_settled": 3,
            "declared_return": 0.020 / 3,
            "realised_return": 0.01,
            "return_bias": 0.01 - 0.020 / 3,
            "close_below_p05": 1 / 3,
            "return_bias_lo": 0.003,
            "return_bias_hi": 0.004,
        }
    )
    assert metrics["settled"] == 3
    assert not any(name.startswith("held_") for name in metrics)


def test_held_claims_return_scores_are_apart() -> None:
    """FORE-OUT-12 / FORE-OUT-10: held returns mirror buys without moving buys."""
    graph = InMemoryGraphStore()
    write_return_ledger(graph)
    buys = card(graph)

    write_return_ledger(graph, held=True)
    combined = card(graph)

    assert {k: v for k, v in combined.metrics.items() if not k.startswith("held_")} == (
        buys.metrics
    )
    for name in RETURN_SCORES:
        assert combined.metrics[f"held_{name}"] == buys.metrics[name]
    assert combined.sample_size == 3


def test_a_claim_or_settlement_without_figures_is_not_return_scored() -> None:
    """FORE-OUT-12: either absent side is counted but never return-scored."""
    graph = InMemoryGraphStore()
    for ticker, claim_figures, settlement_figures in (
        ("AAPL", True, False),
        ("MSFT", False, True),
    ):
        write_return_case(
            graph,
            ticker=ticker,
            as_of="2026-10-21",
            declared=0.010,
            p05=-0.08,
            outcome="target",
            realised=0.07,
            close=0.05,
            claim_figures=claim_figures,
            settlement_figures=settlement_figures,
        )

    metrics = card(graph).metrics

    assert metrics["settled"] == 2
    assert RETURN_SCORES.isdisjoint(metrics)
