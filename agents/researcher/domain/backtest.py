"""Pure walk-forward backtest harness for proposal evidence.

Agent: researcher
Role: simulate scored portfolios with next-close fills and turnover slippage.
External I/O: none.
"""

from __future__ import annotations

from math import ceil, sqrt

from agents.researcher.domain import backtest_types as bt
from contracts.researcher import BacktestEvidence

_TRADING_DAYS = 252.0
_BPS_DENOMINATOR = 10_000.0


def run_walkforward(
    scores: dict[str, dict[str, float]],
    closes: dict[str, list[tuple[str, float]]],
    *,
    top_k: int,
    slippage_bps: float,
    holdout_fraction: float,
) -> bt.BacktestResult:
    """Run a no-lookahead top-K walk-forward simulation."""
    _validate(top_k, slippage_bps, holdout_fraction)
    series = {ticker: bt._Series.from_bars(bars) for ticker, bars in closes.items()}
    dates = sorted(date for date, values in scores.items() if values)
    legs: list[bt.RebalanceLeg] = []
    previous: tuple[str, ...] = ()
    for index, score_date in enumerate(dates[:-1]):
        next_date = dates[index + 1]
        selected = _top(scores[score_date], top_k)
        realized = _realized(scores[score_date], series, score_date, next_date)
        holdings = tuple(ticker for ticker in selected if ticker in realized)
        if not holdings:
            previous = ()
            continue
        gross = sum(realized[ticker] for ticker in holdings) / len(holdings)
        turnover = _turnover(previous, holdings)
        net = gross - slippage_bps / _BPS_DENOMINATOR * turnover
        legs.append(
            bt.RebalanceLeg(
                score_date=score_date,
                exit_score_date=next_date,
                holdings=holdings,
                gross_return=gross,
                net_return=net,
                turnover=turnover,
                fill_count=len(holdings),
                ic=_ic(scores[score_date], realized),
            )
        )
        previous = holdings
    return _result(legs, holdout_fraction)


def to_evidence(result: bt.BacktestResult, *, slippage_bps: float) -> BacktestEvidence:
    """Convert a complete domain result into the review-queue contract type."""
    if result.ic_mean is None:
        raise ValueError("ic_mean is undefined")
    return BacktestEvidence(
        sharpe=result.sharpe,
        ic_mean=result.ic_mean,
        max_drawdown=result.max_drawdown,
        turnover=result.turnover,
        n_days=result.n_days,
        window_start=result.window_start,
        window_end=result.window_end,
        holdout_sharpe=result.holdout_sharpe,
        holdout_ic_mean=result.holdout_ic_mean,
        slippage_bps=slippage_bps,
    )


def _validate(top_k: int, slippage_bps: float, holdout_fraction: float) -> None:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if slippage_bps < 0.0:
        raise ValueError("slippage_bps must be non-negative")
    if not 0.0 < holdout_fraction <= 1.0:
        raise ValueError("holdout_fraction must be in (0, 1]")


def _top(score_map: dict[str, float], top_k: int) -> tuple[str, ...]:
    ranked = sorted(score_map.items(), key=lambda item: (-item[1], item[0]))
    return tuple(ticker for ticker, _ in ranked[:top_k])


def _realized(
    score_map: dict[str, float],
    series: dict[str, bt._Series],
    entry_after: str,
    exit_after: str,
) -> dict[str, float]:
    returns: dict[str, float] = {}
    for ticker in score_map:
        prices = series.get(ticker)
        if prices is None:
            continue
        entry = prices.next_price(entry_after)
        exit_ = prices.next_price(exit_after)
        if entry is None or exit_ is None or entry <= 0.0:
            continue
        returns[ticker] = exit_ / entry - 1.0
    return returns


def _turnover(previous: tuple[str, ...], current: tuple[str, ...]) -> float:
    if not current:
        return 0.0
    if not previous:
        return 1.0
    old = set(previous)
    return len([ticker for ticker in current if ticker not in old]) / len(current)


def _ic(score_map: dict[str, float], realized: dict[str, float]) -> float | None:
    pairs = [(score_map[ticker], value) for ticker, value in realized.items()]
    return _pearson([score for score, _ in pairs], [value for _, value in pairs])


def _result(legs: list[bt.RebalanceLeg], holdout_fraction: float) -> bt.BacktestResult:
    returns = tuple(leg.net_return for leg in legs)
    holdout_count = ceil(len(legs) * holdout_fraction) if legs else 0
    holdout = tuple(legs[-holdout_count:]) if holdout_count else ()
    return bt.BacktestResult(
        returns=returns,
        legs=tuple(legs),
        sharpe=_sharpe(returns),
        max_drawdown=_max_drawdown(returns),
        turnover=_mean([leg.turnover for leg in legs]) or 0.0,
        ic_mean=_mean(_defined_ics(legs)),
        n_days=len(legs),
        window_start=legs[0].score_date if legs else "",
        window_end=legs[-1].exit_score_date if legs else "",
        holdout_sharpe=_sharpe(tuple(leg.net_return for leg in holdout))
        if holdout
        else None,
        holdout_ic_mean=_mean(_defined_ics(holdout)),
        holdout_max_drawdown=_max_drawdown(tuple(leg.net_return for leg in holdout))
        if holdout
        else None,
        holdout_turnover=_mean([leg.turnover for leg in holdout]),
        holdout_n_days=len(holdout),
    )


def _defined_ics(legs: bt.Legs) -> list[float]:
    return [leg.ic for leg in legs if leg.ic is not None]


# Deliberately duplicated tiny statistics helpers; agent islands beat DRY here.
def _mean(values: list[float] | tuple[float, ...]) -> float | None:
    return sum(values) / len(values) if values else None


def _std(values: tuple[float, ...] | list[float]) -> float:
    mean = _mean(values)
    if mean is None:
        return 0.0
    return float((sum((value - mean) ** 2 for value in values) / len(values)) ** 0.5)


def _sharpe(returns: tuple[float, ...]) -> float:
    stdev = _std(returns)
    mean = _mean(returns)
    if stdev == 0.0 or mean is None:
        return 0.0
    return mean / stdev * sqrt(_TRADING_DAYS)


def _max_drawdown(returns: tuple[float, ...]) -> float:
    equity = peak = 1.0
    drawdown = 0.0
    for value in returns:
        equity *= 1.0 + value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity / peak - 1.0)
    return drawdown


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    x_dev = [x - x_mean for x in xs]
    y_dev = [y - y_mean for y in ys]
    x_var = sum(value * value for value in x_dev)
    y_var = sum(value * value for value in y_dev)
    if x_var == 0.0 or y_var == 0.0:
        return None
    cov = sum(x * y for x, y in zip(x_dev, y_dev, strict=True))
    return float(cov / (x_var**0.5 * y_var**0.5))
