"""EXP-014 Appendix P's verdict rule, applied by code (S250).

Agent: tooling
Role: turn intervals and paired differences into EDGE, EDGE IN A PILLAR or NO EDGE.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

BASE_ARM = "base-25"
ABLATION_ARMS = ("technical-only-25", "relative-strength-only-25")
EDGE = "EDGE"
EDGE_IN_A_PILLAR = "EDGE IN A PILLAR"
NO_EDGE = "NO EDGE"
BEHIND = "behind"
INDISTINGUISHABLE = "indistinguishable"

Interval = tuple[float, float]


def decide(
    intervals: Mapping[str, Interval], differences: Mapping[str, Interval]
) -> dict[str, Any]:
    """Appendix P: EDGE, else EDGE IN A PILLAR, else NO EDGE (behind/indistinguishable).

    EDGE: base-25's lower bound > 0. EDGE IN A PILLAR: not EDGE, and an ablation arm's
    lower bound > 0 with the lower bound of its paired difference from base-25 > 0.
    NO EDGE otherwise: behind when base-25's upper bound < 0, indistinguishable when
    its interval contains 0.
    """
    low, high = intervals[BASE_ARM]
    if low > 0:
        return {"verdict": EDGE, "reading": None, "pillars": []}
    pillars = [
        arm
        for arm in ABLATION_ARMS
        if intervals[arm][0] > 0 and differences[arm][0] > 0
    ]
    if pillars:
        return {"verdict": EDGE_IN_A_PILLAR, "reading": None, "pillars": pillars}
    reading = BEHIND if high < 0 else INDISTINGUISHABLE
    return {"verdict": NO_EDGE, "reading": reading, "pillars": []}
