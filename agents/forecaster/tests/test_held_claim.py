"""Sprint 286 A7-A10: held barriers at the claim's own close.

Agent: forecaster
Role: pin declared and rebased prices, named refusals and separate held keys.
External I/O: reads the vocabulary pack; no network.
"""

import json
from pathlib import Path

import pytest

from agents.forecaster.tests.barrier_helpers import (
    barrier_bars,
    barrier_message,
    wire_barrier,
)
from agents.forecaster.tests.held_helpers import held_message
from contracts.forecaster import ShadowPrediction
from kernel import InMemoryGraphStore
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary


def test_a_held_claim_measures_its_barriers_from_its_close() -> None:
    """FORE-OUT-09 / FORE-IN-07: guarded held claim converts dollars on its close."""
    pack = (
        Path(__file__).resolve().parents[3]
        / "orchestration/packs/trading_graph_vocabulary.json"
    )
    guarded = GuardedGraphStore(
        InMemoryGraphStore(),
        Vocabulary.from_mapping(json.loads(pack.read_text("utf-8"))),
    )
    bars = barrier_bars("COP", 760)
    close = bars[-1].close
    bus, graph, sink = wire_barrier(bars=bars, graph=guarded)

    bus.request(held_message("COP", close))

    assert sink.faults == []
    [claim] = graph.list_nodes("BarrierForecast")
    assert claim.key == f"barrier-garch-v1:held:COP:{bars[-1].bar_date}"
    assert claim.props["stop_pct"] == pytest.approx(0.2)
    assert claim.props["target_pct"] == pytest.approx(0.03)
    assert claim.props["subject_kind"] == "position"
    assert claim.props["target_basis"] == "declared"
    assert claim.props["stop_price"] == 0.8 * close
    assert claim.props["target_price"] == 1.03 * close
    assert claim.props["declared_target_pct"] == 0.05
    assert claim.props["entry_close"] == close


def test_past_its_target_a_held_claim_asks_for_the_width_again() -> None:
    """FORE-OUT-09: a name beyond its target gets its declared width again."""
    bars = barrier_bars("COP", 760)
    close = bars[-1].close
    bus, graph, sink = wire_barrier(bars=bars)

    bus.request(
        held_message(
            "COP",
            close,
            features={
                "stop_price": 0.9 * close,
                "target_price": 0.97 * close,
                "target_pct": 0.05,
            },
        )
    )

    assert sink.faults == []
    [claim] = graph.list_nodes("BarrierForecast")
    assert claim.props["target_pct"] == 0.05
    assert claim.props["target_basis"] == "rebased"
    assert claim.props["stop_pct"] == pytest.approx(0.1)


@pytest.mark.parametrize(
    ("change", "severity", "reason"),
    [
        ({"stop_price": None}, "warning", "no live stop"),
        ({"target_price": None}, "warning", "no declared target"),
        ({"stop_price": 1.0}, "warning", "at or below the live stop"),
        ({"target_pct": 0.0}, "error", "must be positive"),
        ({"stop_price": -1.0}, "error", "must be positive"),
        ({"target_price": 2.5}, "error", "outside (0, 1]"),
    ],
    ids=[
        "no-stop",
        "no-target",
        "at-stop",
        "zero-width",
        "negative-stop",
        "wide-target",
    ],
)
def test_what_a_held_claim_cannot_stand_on_is_refused(
    change: dict[str, float | None],
    severity: str,
    reason: str,
) -> None:
    """FORE-FAIL-04: designed gaps warn; malformed prices error; neither claims."""
    bars = barrier_bars("COP", 760)
    close = bars[-1].close
    features = {
        "stop_price": 0.8 * close,
        "target_price": 1.03 * close,
        "target_pct": 0.05,
    }
    for name, value in change.items():
        if value is None:
            features.pop(name)
        else:
            features[name] = value if name == "target_pct" else value * close
    bus, graph, sink = wire_barrier(bars=bars)

    reply = ShadowPrediction.model_validate(
        bus.request(held_message("COP", close, features=features)).payload
    )

    assert graph.list_nodes("BarrierForecast") == ()
    [fault] = sink.faults
    assert fault.severity == severity
    assert reason in fault.message
    assert (reply.value, reply.confidence) == (0.5, 0.0)


def test_a_buy_and_a_held_claim_on_one_bar_both_stand() -> None:
    """FORE-IDM-04: same-bar buy and held COP claims have distinct ledger keys."""
    bars = barrier_bars("COP", 760)
    bus, graph, sink = wire_barrier(bars=bars)

    bus.request(barrier_message("COP"))
    bus.request(held_message("COP", bars[-1].close))

    assert sink.faults == []
    assert {claim.key for claim in graph.list_nodes("BarrierForecast")} == {
        f"barrier-garch-v1:COP:{bars[-1].bar_date}",
        f"barrier-garch-v1:held:COP:{bars[-1].bar_date}",
    }
