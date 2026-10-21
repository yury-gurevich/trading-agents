"""Sprint 288 A4-A6: guarded buy/held returns and additive reruns.

Agent: forecaster
Role: replay each claim's recorded inputs and prove its one simulation and upgrade.
External I/O: reads the local vocabulary pack; no network.
"""

from datetime import date
from unittest.mock import patch

from agents.forecaster.domain import barrier_garch
from agents.forecaster.tests.barrier_helpers import (
    barrier_bars,
    barrier_message,
    wire_barrier,
)
from agents.forecaster.tests.held_helpers import held_message
from agents.forecaster.tests.s288_return_fixtures import (
    RETURN_FIELDS,
    assert_claim_figures,
    guarded_graph,
)


def test_a_claim_states_its_return_from_the_paths_its_probabilities_counted() -> None:
    """FORE-OUT-11 / FORE-IDM-04: one seeded simulation feeds all seven figures."""
    bars = barrier_bars("AAPL", 760, drift=0.0004, end=date(2026, 10, 21))
    bus, graph, sink = wire_barrier(bars=bars, graph=guarded_graph())
    with patch(
        "agents.forecaster.barrier_forecast.garch_paths",
        wraps=barrier_garch.garch_paths,
    ) as simulate:
        bus.request(barrier_message("AAPL", stop_pct=0.05, target_pct=0.06))
    assert sink.faults == []
    assert simulate.call_count == 1
    [claim] = graph.list_nodes("BarrierForecast")
    assert_claim_figures(claim, bars)
    assert -0.05 <= claim.props["expected_return"] <= 0.06
    assert claim.props["close_return_p05"] < 0
    assert 1 <= claim.props["sessions_to_target"] <= 10
    assert 1 <= claim.props["sessions_to_stop"] <= 10


def test_a_held_claim_states_its_return_too() -> None:
    """FORE-OUT-11 / FORE-OUT-09: a guarded held COP claim replays its own widths."""
    bars = barrier_bars("COP", 760, end=date(2026, 10, 21))
    bus, graph, sink = wire_barrier(bars=bars, graph=guarded_graph())

    bus.request(held_message("COP", bars[-1].close))

    assert sink.faults == []
    [claim] = graph.list_nodes("BarrierForecast")
    assert claim.key.startswith("barrier-garch-v1:held:COP:")
    assert claim.props["stop_price"] == 0.8 * bars[-1].close
    assert claim.props["target_price"] == 1.03 * bars[-1].close
    assert claim.props["declared_target_pct"] == 0.05
    assert_claim_figures(claim, bars)


def test_a_claim_stated_before_its_figures_gains_them_on_a_rerun() -> None:
    """FORE-IDM-04 / FORE-OUT-11: an old same-bar claim gains figures and keeps time."""
    bars = barrier_bars("AAPL", 760, drift=0.0004, end=date(2026, 10, 21))
    bus, first_graph, sink = wire_barrier(bars=bars, graph=guarded_graph())
    bus.request(barrier_message("AAPL"))
    assert sink.faults == []
    [first] = first_graph.list_nodes("BarrierForecast")
    expected = {name: first.props[name] for name in RETURN_FIELDS}
    old_props = {
        name: value for name, value in first.props.items() if name not in expected
    }
    old_props["created_at"] = "2026-10-20T22:31:00+00:00"
    fresh = guarded_graph()
    fresh.merge_node(first.label, first.key, old_props)
    bus, graph, sink = wire_barrier(bars=bars, graph=fresh)

    bus.request(barrier_message("AAPL"))

    assert sink.faults == []
    [rerun] = graph.list_nodes("BarrierForecast")
    assert rerun.key == first.key
    assert rerun.props["created_at"] == "2026-10-20T22:31:00+00:00"
    assert rerun.props["model_version"] == "1.0.0"
    assert {name: rerun.props[name] for name in RETURN_FIELDS} == expected
