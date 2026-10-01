"""S250: Appendix P's verdict rule, from intervals given directly.

Agent: tooling
Role: prove EDGE, EDGE IN A PILLAR (both conditions) and both NO EDGE readings.
External I/O: none.
"""

from __future__ import annotations

import pytest
from scripts.replay_verdict_rule import decide

TECH, RS = "technical-only-25", "relative-strength-only-25"
LOSING = (-3.0, -0.5)


def _intervals(base: tuple[float, float], tech=LOSING, rs=LOSING) -> dict:
    return {"base-25": base, TECH: tech, RS: rs}


CASES = {
    "edge": (
        _intervals((0.1, 5.0)),
        {TECH: LOSING, RS: LOSING},
        {"verdict": "EDGE", "reading": None, "pillars": []},
    ),
    "edge beats a pillar too": (
        _intervals((0.1, 5.0), tech=(1.0, 6.0)),
        {TECH: (0.5, 2.0), RS: LOSING},
        {"verdict": "EDGE", "reading": None, "pillars": []},
    ),
    "pillar, both conditions": (
        _intervals((-1.0, 3.0), tech=(0.5, 4.0)),
        {TECH: (0.2, 3.0), RS: LOSING},
        {"verdict": "EDGE IN A PILLAR", "reading": None, "pillars": [TECH]},
    ),
    "pillar, both ablations": (
        _intervals((-6.0, -1.0), tech=(0.5, 4.0), rs=(0.1, 2.0)),
        {TECH: (2.0, 9.0), RS: (1.0, 6.0)},
        {"verdict": "EDGE IN A PILLAR", "reading": None, "pillars": [TECH, RS]},
    ),
    "own bound alone is no pillar": (
        _intervals((-1.0, 3.0), rs=(0.5, 4.0)),
        {TECH: LOSING, RS: (-0.2, 3.0)},
        {"verdict": "NO EDGE", "reading": "indistinguishable", "pillars": []},
    ),
    "paired bound alone is no pillar": (
        _intervals((-1.0, 3.0), rs=(-0.5, 4.0)),
        {TECH: LOSING, RS: (0.2, 3.0)},
        {"verdict": "NO EDGE", "reading": "indistinguishable", "pillars": []},
    ),
    "behind": (
        _intervals((-5.0, -0.1)),
        {TECH: LOSING, RS: LOSING},
        {"verdict": "NO EDGE", "reading": "behind", "pillars": []},
    ),
    "indistinguishable": (
        _intervals((-1.0, 1.0)),
        {TECH: LOSING, RS: LOSING},
        {"verdict": "NO EDGE", "reading": "indistinguishable", "pillars": []},
    ),
    "a lower bound of exactly 0 is not above 0": (
        _intervals((0.0, 2.0), tech=(0.0, 3.0)),
        {TECH: (0.0, 1.0), RS: LOSING},
        {"verdict": "NO EDGE", "reading": "indistinguishable", "pillars": []},
    ),
    "an upper bound of exactly 0 contains 0": (
        _intervals((-2.0, 0.0)),
        {TECH: LOSING, RS: LOSING},
        {"verdict": "NO EDGE", "reading": "indistinguishable", "pillars": []},
    ),
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_c11_the_verdict_rule(case: str) -> None:
    """S250-C11: Appendix P; a pillar needs its own and its paired lower bound > 0."""
    intervals, differences, expected = CASES[case]
    assert decide(intervals, differences) == expected
