"""The daily brief's words: a pure function of the facts one fire selected.

Agent: orchestration
Role: word the operator's once-a-day Telegram brief; the only place a line is worded.
External I/O: none (zone data is read through zoneinfo).

The composer takes no graph and reads no clock, so every line can be proven from a
`BriefFacts` alone (DL-231). Amounts are integer cents here; nothing is recomputed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

if TYPE_CHECKING:
    from datetime import datetime

NOT_FINISHED = "NOT_FINISHED"  # the RED brief's word: no Snapshot by the last fire
_MINUS = chr(0x2212)  # the typographic minus the dashboard prints
_SEP = " · "
_GREEN, _AMBER, _RED = "\U0001f7e2", "\U0001f7e1", "\U0001f534"
_COLOURS = {"PASS": _GREEN, "NO_TRADE": _GREEN, "UNPROVEN": _AMBER}
_BOUNDS = {"buy": "≤", "sell": "≥"}  # a limit is the worst price the order accepts


class BriefDataError(ValueError):
    """A fact the brief needs is malformed; the message names a field, never a value."""


@dataclass(frozen=True)
class OrderLine:
    """One order this run put to the broker, as its Fill records it."""

    side: str
    quantity: int
    ticker: str
    limit_cents: int | None = None
    rejected: bool = False


@dataclass(frozen=True)
class FillLine:
    """One order or stop the broker filled since the previous briefed run."""

    side: str
    quantity: int
    ticker: str
    price_cents: int | None = None
    stopped_out: bool = False


@dataclass(frozen=True)
class BriefFacts:
    """Everything one brief says, selected from the graph and nothing else."""

    verdict: str
    run_id: str
    stamp: str
    degraded: bool = False
    equity_cents: int | None = None
    previous_run: str | None = None
    previous_cents: int | None = None
    scoreboard: str | None = None
    orders: tuple[OrderLine, ...] = ()
    fills: tuple[FillLine, ...] = ()
    open_incidents: int = 0
    critical_flags: int = 0
    last_stage: str | None = None


def compose_brief(facts: BriefFacts) -> str:
    """Return the plain-text message; a run with no report gets the RED brief."""
    if facts.verdict == NOT_FINISHED:
        stage = (
            f"Last stage finished: {facts.last_stage}"
            if facts.last_stage
            else "No stage finished"
        )
        return "\n".join(
            (_header(facts), stage, _orders(facts.orders), _needs_you(facts))
        )
    return "\n".join(
        (
            _header(facts),
            _money(facts),
            facts.scoreboard or "Scoreboard: not in this run's report",
            _orders(facts.orders),
            _fills(facts.fills),
            _needs_you(facts),
        )
    )


def local_stamp(now: datetime, timezone: str) -> str:
    """Name the fire's time in the operator's zone, or in UTC without zone data."""
    try:
        zone = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        return f"{_day(now.astimezone(UTC))} UTC"
    return _day(now.astimezone(zone))


def dollars(cents: int) -> str:
    """Return ``$101,976.32`` from integer cents."""
    whole, part = divmod(abs(cents), 100)
    return f"{_MINUS if cents < 0 else ''}${whole:,}.{part:02d}"


def signed_dollars(cents: int) -> str:
    """Return a change with its sign: a plus, the typographic minus, or none at 0."""
    if cents < 0:
        return f"{_MINUS}{dollars(-cents)}"
    return f"+{dollars(cents)}" if cents else dollars(0)


def _day(moment: datetime) -> str:
    return f"{moment:%a} {moment.day} {moment:%b %H:%M}"


def _header(facts: BriefFacts) -> str:
    colour = _COLOURS.get(facts.verdict, _RED)
    words = (
        f"{colour} {facts.verdict.replace('_', ' ')}",
        facts.run_id,
        facts.stamp,
        *(("degraded",) if facts.degraded else ()),
    )
    return _SEP.join(words)


def _money(facts: BriefFacts) -> str:
    if facts.equity_cents is None:
        return "Equity: not in this run's report"
    if facts.previous_cents is None:
        change = "no earlier figure"
    else:
        delta = facts.equity_cents - facts.previous_cents
        change = f"{signed_dollars(delta)} since {facts.previous_run}"
    return f"Equity {dollars(facts.equity_cents)} ({change})"


def _orders(orders: tuple[OrderLine, ...]) -> str:
    return f"Orders: {_SEP.join(_order(item) for item in orders) or 'none'}"


def _order(item: OrderLine) -> str:
    text = f"{item.side.upper()} {item.quantity} {item.ticker}"
    bound = _BOUNDS.get(item.side)
    if bound is not None and item.limit_cents is not None:
        text += f" {bound} {dollars(item.limit_cents)}"
    return f"{text} rejected" if item.rejected else text


def _fills(fills: tuple[FillLine, ...]) -> str:
    return f"Filled: {_SEP.join(_fill(item) for item in fills) or 'none'}"


def _fill(item: FillLine) -> str:
    text = f"{item.side.upper()} {item.quantity} {item.ticker}"
    if item.price_cents is not None:
        text += f" @ {dollars(item.price_cents)}"
    return f"{text} stopped out" if item.stopped_out else text


def _needs_you(facts: BriefFacts) -> str:
    parts = [
        _count(facts.open_incidents, "open incident"),
        _count(facts.critical_flags, "critical flag"),
    ]
    return f"Needs you: {_SEP.join(part for part in parts if part) or 'nothing'}"


def _count(number: int, noun: str) -> str:
    if not number:
        return ""
    return f"{number} {noun}{'' if number == 1 else 's'}"
