"""The daily brief's book lines: what the held names stand to gain and lose.

Agent: orchestration
Role: word `book_odds`' totals as the brief's two book lines (DL-311, `DSP-OUT-10`):
      the names past their declared target, their gain now and at their stops; then
      the forecast's expected count of names at target first, stop first and
      neither, the names likelier to stop, and the names with no forecast.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.daily_brief_text import signed_dollars

if TYPE_CHECKING:
    from orchestration.book_odds import BookOdds

_SEP = " · "
#: How many names a part of the odds line names before it counts the rest.
LEANING_NAMED = 3
UNFORECAST_NAMED = 4


def book_lines(odds: BookOdds | None) -> tuple[str, ...]:
    """The book line, and the odds line when a claim exists; nothing with no book."""
    if odds is None:
        return ()
    held = f"Book: {len(odds.names)} held"
    if not odds.forecast:
        return (f"{held}{_SEP}no forecast for {odds.as_of.isoformat()}",)
    return (f"{held}{_SEP}{_passed(odds)}", _odds(odds))


def _passed(odds: BookOdds) -> str:
    passed = odds.passed
    if not passed:
        return "none past its target"
    gain = sum(name.gain_cents(claim) for name, claim in passed)
    above = sum(name.above_target_cents(claim) for name, claim in passed)
    at_stops = gain - sum(name.to_stop_cents(claim) for name, claim in passed)
    return (
        f"{len(passed)} past their target: {signed_dollars(gain)} now "
        f"({signed_dollars(above)} above target), "
        f"{signed_dollars(at_stops)} at their stops"
    )


def _odds(odds: BookOdds) -> str:
    target, stop, neither = odds.expected()
    horizon = "/".join(str(sessions) for sessions in odds.horizons)
    parts = [
        f"Odds, next {horizon} sessions, {len(odds.forecast)} names (not yet scored): "
        f"target first {target:.1f}",
        f"stop first {stop:.1f}",
        f"neither {neither:.1f}",
    ]
    leaning = [f"{ticker} {round(p * 100)} %" for ticker, p in odds.leaning_to_stop]
    if leaning:
        parts.append(f"likelier to stop: {_named(leaning, LEANING_NAMED)}")
    if odds.unforecast:
        parts.append(f"no forecast: {_named(list(odds.unforecast), UNFORECAST_NAMED)}")
    return _SEP.join(parts)


def _named(items: list[str], limit: int) -> str:
    named = ", ".join(items[:limit])
    rest = len(items) - limit
    return f"{named} and {rest} more" if rest > 0 else named
