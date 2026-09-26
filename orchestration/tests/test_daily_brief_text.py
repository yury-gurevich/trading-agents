"""S234 composer: the brief's words from its facts alone, with no graph and no clock.

Agent: orchestration
Role: prove money, orders, fills, colours, counts and time are each worded one way.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from orchestration.daily_brief_text import (
    BriefFacts,
    FillLine,
    OrderLine,
    compose_brief,
    dollars,
    local_stamp,
    signed_dollars,
)
from orchestration.tests.daily_brief_scenarios import A1_TEXT, MINUS

_A1 = BriefFacts(
    verdict="PASS",
    run_id="sched-2026-09-25",
    stamp="Sat 26 Sep 08:50",
    equity_cents=10_197_632,
    previous_run="sched-2026-09-24",
    previous_cents=10_200_072,
    scoreboard="vs SPY: -0.43 pts over 33 sessions at 21% invested",
)


def test_the_measured_run_reads_exactly_as_specified() -> None:
    """DSP-OUT-06: sched-2026-09-25's facts compose to the brief S234 specified."""
    assert compose_brief(_A1) == A1_TEXT


def test_a9_money_is_integer_cents_with_separators_and_a_signed_change() -> None:
    """DSP-OUT-06: amounts print from integer cents; the change carries its sign.

    A gain is `+`, a loss the typographic minus, no change unsigned; no reference
    figure says so rather than inventing a zero.
    """
    assert dollars(10_197_632) == "$101,976.32"
    assert dollars(5) == "$0.05"
    assert dollars(-5) == f"{MINUS}$0.05"
    assert signed_dollars(-2_440) == f"{MINUS}$24.40"
    assert signed_dollars(123_456) == "+$1,234.56"
    assert signed_dollars(0) == "$0.00"
    gain = replace(_A1, previous_cents=10_000_000)
    first = replace(_A1, previous_run=None, previous_cents=None)
    assert compose_brief(gain).splitlines()[1] == (
        "Equity $101,976.32 (+$1,976.32 since sched-2026-09-24)"
    )
    assert (
        compose_brief(first).splitlines()[1] == "Equity $101,976.32 (no earlier figure)"
    )


def test_a9_orders_and_fills_read_as_the_broker_holds_them() -> None:
    """DSP-OUT-06: a limit is the bound the order accepts; a stop fill is stopped out.

    A buy's limit is a ceiling, a sell's a floor, and a side with no bound prints
    none; a fill without a broker price prints no price.
    """
    orders = (
        OrderLine("buy", 16, "BMY", 6182),
        OrderLine("sell", 10, "XOM", 11_000),
        OrderLine("buy", 5, "T", rejected=True),
        OrderLine("short", 3, "Z", 100),
    )
    fills = (
        FillLine("buy", 16, "BMY", 6175),
        FillLine("sell", 20, "KO", 5810, stopped_out=True),
        FillLine("buy", 1, "Q"),
    )

    brief = compose_brief(replace(_A1, orders=orders, fills=fills)).splitlines()

    assert brief[3] == (
        "Orders: BUY 16 BMY ≤ $61.82 · SELL 10 XOM ≥ $110.00 · BUY 5 T rejected"
        " · SHORT 3 Z"
    )
    assert brief[4] == (
        "Filled: BUY 16 BMY @ $61.75 · SELL 20 KO @ $58.10 stopped out · BUY 1 Q"
    )


@pytest.mark.parametrize(
    ("verdict", "head"),
    [
        ("PASS", "\U0001f7e2 PASS"),
        ("NO_TRADE", "\U0001f7e2 NO TRADE"),
        ("UNPROVEN", "\U0001f7e1 UNPROVEN"),
        ("FAIL", "\U0001f534 FAIL"),
    ],
)
def test_the_header_colour_is_the_verdicts(verdict: str, head: str) -> None:
    """DSP-OUT-06: green for PASS and NO_TRADE, amber UNPROVEN, red FAIL."""
    brief = compose_brief(replace(_A1, verdict=verdict))

    assert brief.startswith(f"{head} · sched-2026-09-25 · Sat 26 Sep 08:50\n")


def test_needs_you_counts_read_as_words() -> None:
    """DSP-OUT-06: one incident is singular, several flags are plural."""
    one = compose_brief(replace(_A1, open_incidents=1))
    three = compose_brief(replace(_A1, critical_flags=3))

    assert one.endswith("\nNeeds you: 1 open incident")
    assert three.endswith("\nNeeds you: 3 critical flags")


def test_the_time_is_the_operators_and_utc_without_zone_data() -> None:
    """DSP-OUT-06: the fire's time is Melbourne's, following daylight saving.

    Without usable zone data the stamp says UTC, as the hold notice's deadline does.
    """
    friday = datetime(2026, 9, 25, 22, 50, tzinfo=UTC)
    monday = datetime(2026, 10, 5, 22, 50, tzinfo=UTC)

    assert local_stamp(friday, "Australia/Melbourne") == "Sat 26 Sep 08:50"
    assert local_stamp(monday, "Australia/Melbourne") == "Tue 6 Oct 09:50"
    assert local_stamp(friday, "Mars/Olympus") == "Fri 25 Sep 22:50 UTC"
