"""Forecaster sentiment aggregation — pure reducers over per-headline scores.

Agent: forecaster
Role: reduce per-headline model scores to one advisory 0-1 reading and align a
      classifier label/probability to that same 0-1 scale.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Midpoint of the 0-1 sentiment scale — "no signal" / neutral tone.
NEUTRAL = 0.5


@dataclass(frozen=True)
class ModelReading:
    """One model's advisory 0-1 sentiment reading for a subject."""

    value: float
    confidence: float


def align_label(label: str, probability: float) -> float:
    """Map a classifier ``(label, probability)`` to a 0-1 score around neutral.

    Positive tone pushes above 0.5, negative below, neutral/unknown stays at 0.5 —
    the same 0-1 scale the lexicon champion and provider challenger already use.
    """
    normalized = label.strip().lower()
    if normalized == "positive":
        return NEUTRAL + NEUTRAL * probability
    if normalized == "negative":
        return NEUTRAL - NEUTRAL * probability
    return NEUTRAL


def aggregate(
    scores: tuple[float, ...], headlines_for_full_confidence: int
) -> ModelReading | None:
    """Reduce per-headline 0-1 scores to a mean value + count-based confidence.

    Returns ``None`` when there is nothing to score (the caller substitutes a
    neutral, zero-confidence reading). Confidence grows with the headline count
    and saturates at ``headlines_for_full_confidence``.
    """
    if not scores:
        return None
    value = sum(scores) / len(scores)
    confidence = min(len(scores) / max(headlines_for_full_confidence, 1), 1.0)
    return ModelReading(value=value, confidence=confidence)
