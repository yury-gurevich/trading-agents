"""One definition of a held position's decided stop (S230, DL-222/DL-223).

Agent: contracts
Role: prove the resolver reads PM lineage and that all three readers agree on it.
External I/O: none.

Measured 2026-09-25: all 25 broker stops rested 5 % below entry while the PM had
decided 3.90-7.29 % for every buy since 2026-09-05, because broker-adopted
Positions carry the monitor's 5 % fallback and every reader trusted the node.
"""

from __future__ import annotations

import pytest

from agents.execution.broker_stop_thresholds import broker_stop_thresholds
from agents.execution.tests.stop_realign_helpers import (
    DECIDED_STOP_CENTS,
    DECIDED_STOP_PCT,
    FALLBACK_STOP_PCT,
    LINEAGE_RUN,
    seed_adopted_usb,
    seed_buy,
    seed_usb,
)
from agents.monitor.domain.positions import exit_position
from contracts.positions import open_position_stop_thresholds
from contracts.stop_rule import stop_price_cents
from contracts.stop_width import decided_stop_pct
from kernel import InMemoryGraphStore


def test_the_resolver_returns_the_width_the_pm_decided() -> None:
    """EXEC-OBS-06: A1 - the fallback is only for positions with no PM lineage.

    The adopted Position says 0.05; the one filled production buy that equals it
    exactly executes an OrderIntent that decided 0.0402588750356905.
    """
    graph = InMemoryGraphStore()
    position = seed_usb(graph)

    assert decided_stop_pct(graph, position, fallback=FALLBACK_STOP_PCT) == (
        DECIDED_STOP_PCT,
        "lineage",
    )


def test_all_three_readers_agree_on_the_decided_stop() -> None:
    """EXEC-OBS-06: A4 - analyst, execution and monitor read one resolver.

    The analyst's held-stop inputs, execution's placement threshold and the
    monitor's watchdog each report the same width and the same 5806-cent stop.
    """
    graph = InMemoryGraphStore()
    position = seed_usb(graph)

    analyst = open_position_stop_thresholds(graph)[0]
    execution = broker_stop_thresholds(graph, fallback_stop_pct=FALLBACK_STOP_PCT)
    planned = execution.plans[0].threshold
    watchdog = exit_position(graph, position)

    readings = {
        (item.stop_pct, stop_price_cents(item.opened_price_cents, item.stop_pct))
        for item in (analyst, planned, watchdog)
    }
    assert readings == {(DECIDED_STOP_PCT, DECIDED_STOP_CENTS)}
    assert execution.plans[0].stop_pct_source == "lineage"


def test_an_older_lot_of_another_size_does_not_match() -> None:
    """EXEC-OBS-06: A2 - only the buy equal in quantity and price is lineage."""
    graph = InMemoryGraphStore()
    seed_buy(
        graph,
        "pm-run-older",
        quantity=15,
        stop_pct=0.0713,
        submitted_at="2026-09-10T22:40:00+00:00",
    )
    position = seed_usb(graph)

    assert decided_stop_pct(graph, position) == (DECIDED_STOP_PCT, "lineage")


def test_no_exact_match_falls_back_and_says_so() -> None:
    """EXEC-OBS-06: A3 - a holding spanning two lots is never guessed across."""
    graph = InMemoryGraphStore()
    seed_buy(graph, LINEAGE_RUN)
    seed_buy(graph, "pm-run-second", submitted_at="2026-09-19T22:40:00+00:00")
    position = seed_adopted_usb(graph, quantity=32)

    assert decided_stop_pct(graph, position, fallback=0.09) == (
        FALLBACK_STOP_PCT,
        "fallback",
    )


def test_a_fill_path_position_keeps_its_own_width() -> None:
    """EXEC-OBS-06: A5 - a Position the monitor opened from a fill is its own source."""
    graph = InMemoryGraphStore()
    position = graph.merge_node(
        "Position",
        "pm-run-abc:DOW",
        {
            "ticker": "DOW",
            "quantity": 40,
            "opened_price_cents": 2797,
            "stop_pct": 0.0713,
        },
    )

    assert decided_stop_pct(graph, position) == (0.0713, "position")


def test_an_exact_buy_that_decided_no_width_is_not_lineage() -> None:
    """EXEC-OBS-06: no decided width on the matching OrderIntent means fallback."""
    graph = InMemoryGraphStore()
    seed_buy(graph, LINEAGE_RUN, stop_pct=None)
    position = seed_adopted_usb(graph)

    assert decided_stop_pct(graph, position) == (FALLBACK_STOP_PCT, "fallback")


def test_a_verification_fill_is_never_lineage() -> None:
    """EXEC-OBS-06: only pm-run fills are production lineage (spec trap)."""
    graph = InMemoryGraphStore()
    seed_buy(graph, "verify-s230-1")
    position = seed_adopted_usb(graph)

    assert decided_stop_pct(graph, position) == (FALLBACK_STOP_PCT, "fallback")


def test_a_position_with_no_width_needs_a_fallback() -> None:
    """EXEC-OBS-06: a caller's fallback covers only a Position with no width at all."""
    graph = InMemoryGraphStore()
    bare = graph.merge_node("Position", "bare:USB", {"ticker": "USB", "quantity": 1})
    flagged = graph.merge_node("Position", "flag:USB", {"stop_pct": True})

    assert decided_stop_pct(graph, bare, fallback=0.06) == (0.06, "fallback")
    with pytest.raises(ValueError, match="no stop width"):
        decided_stop_pct(graph, bare)
    with pytest.raises(TypeError):
        decided_stop_pct(graph, flagged)
