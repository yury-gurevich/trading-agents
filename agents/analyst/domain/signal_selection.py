"""Top-signal selection: pick the most influential, pillar-diverse signals.

Agent: analyst
Role: rank a recommendation's per-signal sub-scores by weighted contribution and
select a small, pillar-diverse subset to surface in the rationale.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass

# Neutral midpoint of every 0-100 sub-score: a signal's influence is its distance
# from neutral, weighted by its pillar. This is the rule, not tunable policy.
_NEUTRAL = 50.0


@dataclass(frozen=True)
class Signal:
    """One named, pillar-tagged 0-100 sub-score (50 = neutral)."""

    name: str
    pillar: str
    score: float


def technical_signals(metrics: dict[str, float]) -> list[Signal]:
    """Extract technical signals from a score-metrics dict (``<name>_score`` keys)."""
    suffix = "_score"
    return [
        Signal(name=key[: -len(suffix)], pillar="technical", score=value)
        for key, value in metrics.items()
        if key.endswith(suffix)
    ]


def fundamental_signals(metrics: dict[str, float]) -> list[Signal]:
    """Extract fundamental signals; drops ``*_available`` meta keys."""
    return [
        Signal(name=key, pillar="fundamental", score=value)
        for key, value in metrics.items()
        if not key.endswith("_available")
    ]


def _contribution(signal: Signal, weights: dict[str, float]) -> float:
    """Weighted distance from neutral; an unweighted pillar contributes nothing."""
    return abs(signal.score - _NEUTRAL) * weights.get(signal.pillar, 0.0)


def _rank_key(signal: Signal, weights: dict[str, float]) -> tuple[float, float]:
    """Sort key: weighted contribution, then raw distance from neutral (tie-break)."""
    return _contribution(signal, weights), abs(signal.score - _NEUTRAL)


def select_top_signals(
    signals: list[Signal],
    weights: dict[str, float],
    *,
    slack: float,
    max_signals: int,
) -> tuple[Signal, ...]:
    """Select up to ``max_signals`` signals by weighted contribution, favouring pillars.

    Signals are ranked by ``|score - 50| * pillar_weight`` (ties broken by raw
    distance from neutral). Selection then walks the ranking, but at each step prefers
    the highest-ranked signal from a **not-yet-used pillar** whose contribution is
    within ``slack`` of the current best — so a strong-enough signal from a fresh
    pillar is surfaced ahead of another from a pillar already represented.
    """
    ranked = sorted(
        signals,
        key=lambda signal: _rank_key(signal, weights),
        reverse=True,
    )
    selected: list[Signal] = []
    used_pillars: set[str] = set()
    remaining = list(ranked)
    while remaining and len(selected) < max_signals:
        best_contribution = _contribution(remaining[0], weights)
        pick = next(
            (
                signal
                for signal in remaining
                if signal.pillar not in used_pillars
                and _contribution(signal, weights) + slack >= best_contribution
            ),
            remaining[0],
        )
        selected.append(pick)
        used_pillars.add(pick.pillar)
        remaining.remove(pick)
    return tuple(selected)
