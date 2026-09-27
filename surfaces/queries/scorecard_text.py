"""Plain words for the unattended scorecard: the tile, its detail and the answer.

Agent: surfaces
Role: word and colour the scorecard once, for the dashboard tile, the chat and MCP.
External I/O: none.

Shares are shown rounded down, so a share read at or above its goal is at or above it;
the tone is decided on the exact ratios (DL-235 decision 9). No sprint, design-log,
drift or law id appears in any text here (SRF-OUT-05).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from surfaces.queries.scorecard_model import Scorecard, SessionRow

# What the graph does not record: named in every answer, never guessed (S236 row 10).
NOT_COUNTED = (
    "broker orders placed or cancelled by hand",
    "Azure changes other than a recorded deploy",
    "graph repairs made by scripts",
)
_KINDS = {
    "command": ("command", "commands"),
    "run": ("run started by hand", "runs started by hand"),
    "resume": ("resume", "resumes"),
    "hold_answer": ("hold answer", "hold answers"),
    "escalation": ("escalation", "escalations"),
    "deploy": ("deploy", "deploys"),
}


def tone(card: Scorecard) -> str:
    """Red below the completion goal, amber at or above the hands-on line, else green.

    Decided on the exact ratios, never on the rounded-down shares shown.
    """
    goals = card.settings
    if (card.g1 or 0.0) < goals.scorecard_g1_target:
        return "crit"
    if (card.g3 or 0.0) >= goals.scorecard_g3_target:
        return "warn"
    return "good"


def vital_line(card: Scorecard) -> str:
    """Return the status-line text: both clocks, then cycles, then hands-on days."""
    return (
        f"unattended {card.unattended}, untouched {card.untouched} of "
        f"{card.settings.scorecard_clock_sessions} sessions · "
        f"cycles {_percent(card.complete, card.counted)} · "
        f"hands-on {card.hands_on} of {card.healthy} days"
    )


def detail_rows(card: Scorecard) -> list[tuple[str, str]]:
    """Return the labelled numbers shown when the operator opens the tile."""
    goals = card.settings
    target = goals.scorecard_clock_sessions
    first, last = card.sessions[0].day, card.sessions[-1].day
    return [
        (
            "Unattended in a row",
            f"{card.unattended} of {target}: no action but deploys",
        ),
        ("Untouched in a row", f"{card.untouched} of {target}: nothing human at all"),
        ("Cycles completed", _completed(card)),
        ("Hands-on days", _hands_on(card)),
        ("Hands-on, with deploys", f"{card.hands_on_with_deploys} of {card.healthy}"),
        ("Window", f"{_sessions(card.counted)}, {first} to {last}"),
    ]


def session_rows(card: Scorecard) -> list[tuple[str, str]]:
    """Return one row per counted session, newest first: day and word, then actions."""
    return [
        (f"{row.day} {row.verdict.replace('_', ' ')}", _actions(row))
        for row in reversed(card.sessions)
    ]


def summary(card: Scorecard) -> str:
    """Return the answer the chat and the MCP tool give, word for word."""
    if card.status != "measured":
        return f"There is nothing to score yet: {card.reason}."
    goals = card.settings
    return (
        f"Unattended for the last {_sessions(card.unattended)} and untouched for "
        f"{card.untouched}, of the {goals.scorecard_clock_sessions} in a row the "
        f"goal needs; {card.complete} of {card.counted} scheduled sessions completed "
        f"({_percent(card.complete, card.counted)}, goal at least "
        f"{_goal(goals.scorecard_g1_target)}), and {_acted(card)}. Not counted, "
        f"because the graph does not record them: {', '.join(NOT_COUNTED[:-1])}, "
        f"and {NOT_COUNTED[-1]}."
    )


def _completed(card: Scorecard) -> str:
    goal = _goal(card.settings.scorecard_g1_target)
    share = _percent(card.complete, card.counted)
    return f"{card.complete} of {card.counted} ({share}, goal at least {goal})"


def _hands_on(card: Scorecard) -> str:
    if not card.healthy:
        return "no healthy session to judge"
    goal = _goal(card.settings.scorecard_g3_target)
    share = _percent(card.hands_on, card.healthy)
    return f"{card.hands_on} of {card.healthy} healthy ({share}, goal under {goal})"


def _acted(card: Scorecard) -> str:
    if not card.healthy:
        return "no session was healthy, so there is no hands-on share"
    goal = _goal(card.settings.scorecard_g3_target)
    share = _percent(card.hands_on, card.healthy)
    return (
        f"a human acted on {card.hands_on} of {card.healthy} healthy ones ({share}, "
        f"goal under {goal}; {card.hands_on_with_deploys} counting deploys)"
    )


def _actions(row: SessionRow) -> str:
    counted = (
        f"{count} {_KINDS[kind][count != 1]}" for kind, count in row.actions.items()
    )
    return " · ".join(counted) or "no human action"


def _percent(part: int, whole: int) -> str:
    return f"{part * 100 // whole} %"  # rounded down: never reads above the truth


def _goal(share: float) -> str:
    return f"{share * 100:g} %"


def _sessions(count: int) -> str:
    return f"{count} session" if count == 1 else f"{count} sessions"
