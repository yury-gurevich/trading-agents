"""Sprint 288 A7-A9: the outcome's realised return and void's absent figures.

Agent: forecaster
Role: pin settling-close arithmetic, first-touch sessions and guarded persistence.
External I/O: reads the local vocabulary pack; no network.
"""

from datetime import timedelta

import pytest

from agents.forecaster.domain.barrier_settlement import settle
from agents.forecaster.settlement_store import write_settlement
from agents.forecaster.tests.s288_return_fixtures import guarded_graph
from agents.forecaster.tests.settlement_helpers import seed_claim
from agents.forecaster.tests.settlement_paths import AS_OF, path


@pytest.mark.parametrize(
    ("events", "tenth", "outcome", "realised", "close", "session"),
    [
        ({3: (101.0, 94.0)}, 103.0, "stop", -0.05, 0.03, 3),
        ({5: (107.5, 99.0)}, 98.0, "target", 0.07, -0.02, 5),
        ({}, 102.0, "neither", 0.02, 0.02, None),
    ],
    ids=["stop", "target", "neither"],
)
def test_a_settlement_records_the_return_its_outcome_gave(
    events: dict[int, tuple[float, float]],
    tenth: float,
    outcome: str,
    realised: float,
    close: float,
    session: int | None,
) -> None:
    """FORE-OUT-11 / FORE-OUT-08: returns use the settling 100, never claimed 101."""
    result = settle(
        path(events=events, closes={10: tenth}),
        as_of=AS_OF,
        entry_close=101.0,
        stop_pct=0.05,
        target_pct=0.07,
        pass_date=AS_OF + timedelta(days=14),
    )
    assert result is not None
    assert result.outcome == outcome
    assert result.realised_return == pytest.approx(realised)
    assert result.close_return == pytest.approx(close)
    assert result.outcome_session == session
    assert result.entry_close_settling == 100.0
    assert result.entry_ratio == pytest.approx(100.0 / 101.0)


def test_a_session_touching_both_is_the_stop_and_its_session() -> None:
    """FORE-OUT-08 / FORE-OUT-11: both touched on session 4 means stop and -0.05."""
    result = settle(
        path(events={4: (108.0, 94.0)}),
        as_of=AS_OF,
        entry_close=101.0,
        stop_pct=0.05,
        target_pct=0.07,
        pass_date=AS_OF + timedelta(days=14),
    )
    assert result is not None
    assert (result.outcome, result.outcome_session, result.realised_return) == (
        "stop",
        4,
        -0.05,
    )


def test_a_void_settlement_records_no_return() -> None:
    """FORE-FAIL-05 / FORE-OUT-11: split and 45-day voids carry three None figures."""
    split = settle(
        path(closes={3: 50.0}),
        as_of=AS_OF,
        entry_close=101.0,
        stop_pct=0.05,
        target_pct=0.07,
        pass_date=AS_OF + timedelta(days=14),
    )
    missing = settle(
        [],
        as_of=AS_OF,
        entry_close=101.0,
        stop_pct=0.05,
        target_pct=0.07,
        pass_date=AS_OF + timedelta(days=45),
    )
    for result, reason in (
        (split, "suspected_corporate_action"),
        (missing, "no_settling_bars"),
    ):
        assert result is not None
        assert (result.outcome, result.void_reason) == ("void", reason)
        assert result.realised_return is None
        assert result.close_return is None
        assert result.outcome_session is None
    assert split is not None
    graph = guarded_graph()
    claim = seed_claim(graph, entry_close=101.0)
    write_settlement(graph, claim, split, settling_ref="market-data:split")
    [node] = graph.list_nodes("BarrierSettlement")
    for name in ("realised_return", "close_return", "outcome_session"):
        assert node.props[name] is None
