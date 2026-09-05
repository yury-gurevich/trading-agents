"""A proportion that always carries its denominator and its uncertainty.

Agent: orchestration
Role: express "how often did these agree" as a number nobody can quote without
      also quoting how much was compared and how much was thrown away.
External I/O: none.

The interval is Wilson's score interval, not the normal approximation. At the
sample sizes this sprint can afford — tens of comparable pairs, and proportions
that may sit near 0 or 1 — the normal approximation produces bounds outside
[0, 1] and is known to be badly calibrated; Wilson stays inside the interval and
behaves at small n. That is the whole reason for the choice.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = ["Agreement", "wilson_interval"]

_Z95 = 1.959963984540054


def wilson_interval(matched: int, compared: int) -> tuple[float, float] | None:
    """Return the 95% Wilson score interval, or None when nothing was compared."""
    if compared <= 0:
        return None
    proportion = matched / compared
    denominator = 1 + _Z95**2 / compared
    centre = (proportion + _Z95**2 / (2 * compared)) / denominator
    spread = (
        _Z95
        * math.sqrt(
            proportion * (1 - proportion) / compared + _Z95**2 / (4 * compared**2)
        )
        / denominator
    )
    return (max(0.0, centre - spread), min(1.0, centre + spread))


@dataclass(frozen=True)
class Agreement:
    """How often two things agreed, over what, and what was set aside.

    ``excluded`` counts verdicts a real debate never produced — a fail-open or a
    failed replay. ``no_counterpart`` counts real verdicts the *other* source
    never had an opinion on. Conflating the two would let a shrinking overlap
    read as a rising exclusion rate.
    """

    name: str
    matched: int
    compared: int
    excluded: int
    no_counterpart: int = 0

    @property
    def rate(self) -> float | None:
        """The proportion, or None when there was nothing to compare."""
        if self.compared <= 0:
            return None
        return self.matched / self.compared

    @property
    def interval(self) -> tuple[float, float] | None:
        """The 95% Wilson interval around ``rate``."""
        return wilson_interval(self.matched, self.compared)

    def detail(self) -> str:
        """Render the number so it cannot be quoted without its denominator."""
        head = (
            f"{self.name}: matched={self.matched}; compared={self.compared}; "
            f"excluded={self.excluded}; no_counterpart={self.no_counterpart}"
        )
        rate = self.rate
        interval = self.interval
        if rate is None or interval is None:
            return f"{head}; rate=n/a (nothing was compared)"
        low, high = interval
        return (
            f"{head}; rate={rate * 100:.2f}%; "
            f"ci95=[{low * 100:.2f}%, {high * 100:.2f}%]"
        )
