"""Pure scoring primitives for governed researcher factors.

Agent: researcher
Role: compute catalogue factor scores from bar history without I/O.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping

Bars = dict[str, list[tuple[str, float, float]]]
Scores = dict[str, dict[str, float]]
Params = Mapping[str, float]


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
