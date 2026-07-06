"""Bounded factor catalogue for governed researcher proposals.

Agent: researcher
Role: validate catalogue-only factor selections and score bars without I/O.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any, cast

from agents.researcher.domain.factors_impl import (
    mean_reversion_scores,
    momentum_scores,
    volatility_rank_scores,
)
from kernel import tunable

Bars = dict[str, list[tuple[str, float, float]]]
Scores = dict[str, dict[str, float]]
Params = Mapping[str, float]
FactorScorer = Callable[[Bars, Params], Scores]


@dataclass(frozen=True)
class FactorParameter:
    """One tunable-bounded catalogue parameter."""

    default: float
    minimum: float
    maximum: float
    unit: str
    why: str


@dataclass(frozen=True)
class FactorSpec:
    """One selectable factor and its bounded parameter surface."""

    name: str
    summary: str
    parameters: Mapping[str, FactorParameter]
    scorer: FactorScorer


@dataclass(frozen=True)
class FactorSelection:
    """A validated catalogue selection; scoring is still deterministic."""

    name: str
    params: tuple[tuple[str, float], ...]
    rationale: str


def validate_selection(
    name: str, params: Mapping[str, object], *, rationale: str = ""
) -> FactorSelection | None:
    """Return a bounded catalogue selection, or ``None`` for fail-open."""
    spec = CATALOGUE.get(name)
    if spec is None:
        return None
    if set(params) != set(spec.parameters):
        return None
    validated: list[tuple[str, float]] = []
    for param_name, bound in spec.parameters.items():
        value = _number(params[param_name])
        if value is None:
            return None
        if not value.is_integer():
            return None
        if value < bound.minimum:
            return None
        if value > bound.maximum:
            return None
        validated.append((param_name, value))
    return FactorSelection(
        name=name, params=tuple(sorted(validated)), rationale=rationale
    )


def score(selection: FactorSelection, bars: Bars) -> Scores:
    """Score bars through the selected pure factor."""
    return CATALOGUE[selection.name].scorer(bars, dict(selection.params))


def _parameter(
    default: int, *, why: str, ge: int, le: int, unit: str = "bars"
) -> FactorParameter:
    field = tunable(default, why=why, ge=ge, le=le, unit=unit)
    return FactorParameter(
        default=float(field.get_default()),
        minimum=_limit(field, "ge"),
        maximum=_limit(field, "le"),
        unit=str(field.json_schema_extra["unit"]),
        why=str(field.description),
    )


def _limit(field: Any, attr: str) -> float:  # noqa: ANN401 - pydantic metadata.
    return float(
        next(
            value
            for value in (getattr(meta, attr, None) for meta in field.metadata)
            if value is not None
        )
    )


def _number(value: object) -> float | None:
    if type(value) not in (int, float):
        return None
    parsed = float(cast("int | float", value))
    return parsed if isfinite(parsed) else None


CATALOGUE: Mapping[str, FactorSpec] = {
    "momentum": FactorSpec(
        name="momentum",
        summary="Trailing close-to-close return over lookback bars.",
        parameters={
            "lookback": _parameter(
                20,
                why="Momentum needs enough bars to observe trend without overfitting.",
                ge=5,
                le=120,
            )
        },
        scorer=momentum_scores,
    ),
    "mean_reversion": FactorSpec(
        name="mean_reversion",
        summary="Negative z-score of close versus its trailing moving average.",
        parameters={
            "window": _parameter(
                20,
                why="Mean reversion compares the close with a stable trailing window.",
                ge=5,
                le=120,
            )
        },
        scorer=mean_reversion_scores,
    ),
    "volatility_rank": FactorSpec(
        name="volatility_rank",
        summary="Low-volatility tilt using negative realized volatility.",
        parameters={
            "window": _parameter(
                20,
                why="Realized volatility needs a bounded trailing return window.",
                ge=5,
                le=120,
            )
        },
        scorer=volatility_rank_scores,
    ),
}
