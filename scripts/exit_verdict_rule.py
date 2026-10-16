"""EXP-022 Appendix P's arms and verdict rule, applied by code (S282).

Agent: tooling
Role: name the twelve arms and their exits; read each exit arm's paired difference
      from stops-only; decide EXIT WINS, EXIT WINS AT LOW COST or CHAMPION HOLDS.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

from scripts.replay_exits import STOPS_ONLY, ExitPolicy

if TYPE_CHECKING:
    from collections.abc import Mapping

EXPERIMENT = "EXP-022"
START = date(2017, 1, 3)
CHAMPION = "stops"
POLICIES = {
    CHAMPION: STOPS_ONLY,
    "target": ExitPolicy(take_profit=True),
    "time10": ExitPolicy(time_exit_sessions=10),
    "trail": ExitPolicy(trailing_stop=True),
    "target-time10": ExitPolicy(take_profit=True, time_exit_sessions=10),
    "cool5": ExitPolicy(reentry_cooldown_sessions=5),
}
CHALLENGERS = ("target", "time10", "trail", "target-time10", "cool5")
BAR_BPS = 25
LOW_COST_BPS = 10
FAMILIES = (BAR_BPS, LOW_COST_BPS)
EXIT_WINS = "EXIT WINS"
EXIT_WINS_AT_LOW_COST = "EXIT WINS AT LOW COST"
CHAMPION_HOLDS = "CHAMPION HOLDS"
WINS = "wins"
SPLIT = "split"
BEHIND = "behind"
INDISTINGUISHABLE = "indistinguishable"


def arm_name(stem: str, bps: int) -> str:
    """The manifest's name for an arm: `<stem>-<bps>`."""
    return f"{stem}-{bps}"


def expected_arms() -> tuple[str, ...]:
    """Every arm Appendix P names, the 25 bps family first, the champion first."""
    return tuple(arm_name(stem, bps) for bps in FAMILIES for stem in POLICIES)


def reading(difference: Mapping[str, Any]) -> str:
    """wins: lower bound > 0 and each half's point > 0; split: the bound alone.

    behind: the upper bound < 0; indistinguishable: anything else.
    """
    low, high = difference["interval"]
    if low > 0:
        halves_ahead = all(point > 0 for point in difference["halves"])
        return WINS if halves_ahead else SPLIT
    return BEHIND if high < 0 else INDISTINGUISHABLE


def decide(differences: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """EXIT WINS at 25 bps; else EXIT WINS AT LOW COST at 10 bps; else CHAMPION HOLDS.

    The leader is the winning challenger with the largest point difference, the
    first in CHALLENGERS' order on a tie.
    """
    readings = {name: reading(item) for name, item in differences.items()}
    for bps, verdict in ((BAR_BPS, EXIT_WINS), (LOW_COST_BPS, EXIT_WINS_AT_LOW_COST)):
        winners = [s for s in CHALLENGERS if readings[arm_name(s, bps)] == WINS]
        if winners:
            points = {s: differences[arm_name(s, bps)]["point"] for s in winners}
            leader = max(winners, key=points.__getitem__)
            return {
                "verdict": verdict,
                "winners": winners,
                "leader": leader,
                "readings": readings,
            }
    return {
        "verdict": CHAMPION_HOLDS,
        "winners": [],
        "leader": None,
        "readings": readings,
    }
