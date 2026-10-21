"""Sprint 286 A15: held scores leave the S241 buy ledger unchanged.

Agent: forecaster
Role: compare literal buy metrics before and after synthetic held claims arrive.
External I/O: none.
"""

from agents.forecaster.domain.barrier_settlement import Settlement
from agents.forecaster.settlement_store import write_settlement
from agents.forecaster.tests.held_helpers import held_record
from agents.forecaster.tests.ledger_fixture import card, write_ledger
from agents.forecaster.tests.settlement_paths import AS_OF
from kernel import InMemoryGraphStore


def test_held_claims_are_scored_apart_and_the_buys_scores_stand() -> None:
    """FORE-OUT-10: held counts and skill are separate; every buy metric stands."""
    graph = InMemoryGraphStore()
    write_ledger(graph)
    buys_only = card(graph)
    assert not any(name.startswith("held_") for name in buys_only.metrics)
    for ticker, outcome in (("COP", "target"), ("KO", "stop"), ("MO", None)):
        claim = held_record(graph, ticker)
        if outcome is not None:
            write_settlement(
                graph,
                claim,
                Settlement(outcome, None, AS_OF, 100.0, 1.0),
                settling_ref="market-data:held-score-fixture",
            )

    combined = card(graph)

    assert {
        k: v for k, v in combined.metrics.items() if not k.startswith("held_")
    } == buys_only.metrics
    assert combined.sample_size == buys_only.sample_size == 10
    assert combined.metrics["held_settled"] == 2.0
    assert combined.metrics["held_open"] == 1.0
    assert combined.metrics["held_realised_target"] == 0.5
    assert "held_skill" in combined.metrics
