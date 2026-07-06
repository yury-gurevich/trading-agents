"""Governed factor scoring for forecaster shadow signals.

Agent: forecaster
Role: duplicate the approved researcher factor catalogue without cross-agent imports.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import isfinite
from typing import cast

Bars = dict[str, list[tuple[str, float, float]]]
Scores = dict[str, dict[str, float]]
Params = Mapping[str, float]
FactorScorer = Callable[[Bars, Params], Scores]


@dataclass(frozen=True)
class FactorSpec:
    """One approved factor and its bounded integer parameter."""

    name: str
    parameter: str
    minimum: float
    maximum: float
    scorer: FactorScorer


@dataclass(frozen=True)
class FactorSelection:
    """Operator-approved catalogue factor plus validated parameters."""

    name: str
    params: tuple[tuple[str, float], ...]


def validate_selection(
    name: str, params: Mapping[str, object]
) -> FactorSelection | None:
    """Return a bounded factor selection, or None when settings are disabled/bad."""
    spec = CATALOGUE.get(name)
    if spec is None:
        return None
    if set(params) != {spec.parameter}:
        return None
    value = _number(params[spec.parameter])
    if value is None:
        return None
    if not value.is_integer():
        return None
    if value < spec.minimum:
        return None
    if value > spec.maximum:
        return None
    return FactorSelection(name=name, params=((spec.parameter, value),))


def parse_selection(name: str, params_text: str) -> FactorSelection | None:
    """Parse operator settings like ``lookback=60`` into a bounded selection."""
    if not name:
        return None
    params = _parse_params(params_text)
    return validate_selection(name, params) if params is not None else None


def score(selection: FactorSelection, bars: Bars) -> Scores:
    """Score bars with the selected factor."""
    return CATALOGUE[selection.name].scorer(bars, dict(selection.params))


def latest_score(selection: FactorSelection, bars: Bars) -> float | None:
    """Return the newest available factor value."""
    scores = score(selection, bars)
    if not scores:
        return None
    values = tuple(scores[max(scores)].values())
    return sum(values) / len(values)


def model_id(selection: FactorSelection) -> str:
    """Derive the default scorecard key for an enabled factor."""
    return f"factor-{selection.name}-{int(selection.params[0][1])}"


def model_ref(selection: FactorSelection) -> str:
    """Derive stable model lineage metadata for the factor."""
    param, value = selection.params[0]
    return f"factor:{selection.name}:{param}={int(value)}"


def momentum_scores(bars: Bars, params: Params) -> Scores:
    """Score trailing close-to-close return over a bounded lookback."""
    lookback = _period(params["lookback"])
    scores: Scores = {}
    for ticker, rows in bars.items():
        dates, closes = _series(rows)
        for index in range(lookback, len(closes)):
            base = closes[index - lookback]
            if base <= 0.0:
                continue
            scores.setdefault(dates[index], {})[ticker] = closes[index] / base - 1.0
    return scores


def mean_reversion_scores(bars: Bars, params: Params) -> Scores:
    """Score negative z-score versus a bounded trailing average."""
    window = _period(params["window"])
    scores: Scores = {}
    for ticker, rows in bars.items():
        dates, closes = _series(rows)
        for index in range(window - 1, len(closes)):
            trailing = closes[index + 1 - window : index + 1]
            stdev = _std(trailing)
            z_score = 0.0 if stdev == 0.0 else (closes[index] - _mean(trailing)) / stdev
            scores.setdefault(dates[index], {})[ticker] = -z_score
    return scores


def volatility_rank_scores(bars: Bars, params: Params) -> Scores:
    """Score lower realized volatility higher over a bounded trailing window."""
    window = _period(params["window"])
    scores: Scores = {}
    for ticker, rows in bars.items():
        dates, closes = _series(rows)
        for index in range(window - 1, len(closes)):
            trailing = closes[index + 1 - window : index + 1]
            returns = tuple(
                trailing[position] / trailing[position - 1] - 1.0
                for position in range(1, len(trailing))
                if trailing[position - 1] > 0.0
            )
            scores.setdefault(dates[index], {})[ticker] = -_std(returns)
    return scores


def _parse_params(text: str) -> dict[str, object] | None:
    if not text.strip():
        return {}
    params: dict[str, object] = {}
    for item in text.split(","):
        if "=" not in item:
            return None
        name, raw = (part.strip() for part in item.split("=", 1))
        if not name or not raw or name in params:
            return None
        try:
            params[name] = float(raw)
        except ValueError:
            return None
    return params


def _number(value: object) -> float | None:
    if type(value) not in (int, float):
        return None
    parsed = float(cast("int | float", value))
    return parsed if isfinite(parsed) else None


def _period(value: float) -> int:
    return int(value)


def _series(
    rows: list[tuple[str, float, float]],
) -> tuple[tuple[str, ...], tuple[float, ...]]:
    ordered = tuple(sorted(rows, key=lambda item: item[0]))
    return tuple(date for date, _, _ in ordered), tuple(
        close for _, close, _ in ordered
    )


def _mean(values: tuple[float, ...]) -> float:
    return sum(values) / len(values)


def _std(values: tuple[float, ...]) -> float:
    mean = _mean(values)
    return float((sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5)


CATALOGUE: Mapping[str, FactorSpec] = {
    "momentum": FactorSpec("momentum", "lookback", 5.0, 120.0, momentum_scores),
    "mean_reversion": FactorSpec(
        "mean_reversion", "window", 5.0, 120.0, mean_reversion_scores
    ),
    "volatility_rank": FactorSpec(
        "volatility_rank", "window", 5.0, 120.0, volatility_rank_scores
    ),
}
