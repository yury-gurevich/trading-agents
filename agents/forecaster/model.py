"""Forecaster sentiment model port and deterministic fake.

Agent: forecaster
Role: define the per-headline sentiment scoring boundary; isolate heavy ML so the
      gate never imports torch.
External I/O: none (the concrete FinBERT client lives in finbert.py).
"""

from __future__ import annotations

from typing import Protocol

from agents.forecaster.domain.sentiment import NEUTRAL


class SentimentModel(Protocol):
    """Boundary for a per-headline 0-1 sentiment scorer."""

    def score_headlines(self, headlines: tuple[str, ...]) -> tuple[float, ...]:
        """Score each headline in 0-1 (1 most positive), aligned to input order."""
        ...  # pragma: no cover - protocol declaration only.


class FakeSentimentModel:
    """Deterministic per-headline scorer used by the unit gate."""

    def __init__(
        self,
        per_headline: dict[str, float] | None = None,
        default: float = NEUTRAL,
    ) -> None:
        """Store canned per-headline scores; unknown headlines get the default."""
        self._per_headline = per_headline or {}
        self._default = default

    def score_headlines(self, headlines: tuple[str, ...]) -> tuple[float, ...]:
        """Return the canned/default score for each headline, in input order."""
        return tuple(
            self._per_headline.get(headline, self._default) for headline in headlines
        )
