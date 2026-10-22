"""EXP-015's fifteen line features, read only from bars up to each session (S289).

Agent: tooling
Role: turn one line's bars into one array per feature, aligned to its bars; a value
      that needs more history than the line has is NaN.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scripts.exp015_spec import ATR_SESSIONS, DOLLAR_VOLUME_SESSIONS, LINE_FEATURES

if TYPE_CHECKING:
    from collections.abc import Callable


def line_features(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    volumes: np.ndarray,
    spy_closes: np.ndarray,
) -> dict[str, np.ndarray]:
    """The line features by name, per bar; `spy_closes` is SPY on the line's dates."""
    returns = {k: _back_return(closes, k) for k in (5, 20, 60, 120)}
    simple = _back_return(closes, 1)
    logs = np.log(closes / _shift(closes, 1))
    spy_simple = _back_return(spy_closes, 1)
    beta, residual = _beta_residual(simple, spy_simple, 60)
    features = {
        "ret_5": returns[5],
        "ret_20": returns[20],
        "ret_60": returns[60],
        "ret_120": returns[120],
        "ret_252_21": _shift(closes, 21) / _shift(closes, 252) - 1.0,
        "dist_252_high": closes / _trailing(np.max, highs, 252) - 1.0,
        "vol_20": _trailing(_std, logs, 20),
        "vol_60": _trailing(_std, logs, 60),
        "atr_pct": _trailing(np.mean, _true_range(highs, lows, closes), ATR_SESSIONS)
        / closes,
        "beta_60": beta,
        "resvol_60": residual,
        "volratio_5_60": _ratio(
            _trailing(np.mean, volumes, 5), _trailing(np.mean, volumes, 60)
        ),
        "volratio_20_120": _ratio(
            _trailing(np.mean, volumes, 20), _trailing(np.mean, volumes, 120)
        ),
        "dollar_volume": _trailing(np.mean, closes * volumes, DOLLAR_VOLUME_SESSIONS),
        "rs_120": (1.0 + returns[120]) / (1.0 + _back_return(spy_closes, 120)) - 1.0,
    }
    return {name: features[name] for name in LINE_FEATURES}


def _shift(values: np.ndarray, lag: int) -> np.ndarray:
    """values[i - lag] at i, NaN where i < lag."""
    out = np.full(values.shape, np.nan)
    if lag < len(values):
        out[lag:] = values[: len(values) - lag]
    return out


def _back_return(values: np.ndarray, lag: int) -> np.ndarray:
    return values / _shift(values, lag) - 1.0


def _trailing(
    reduce: Callable[..., np.ndarray], values: np.ndarray, window: int
) -> np.ndarray:
    """The trailing reduce over `window` values; NaN before a full window or a NaN."""
    out = np.full(values.shape, np.nan)
    if len(values) >= window:
        out[window - 1 :] = reduce(sliding_window_view(values, window), axis=1)
    return out


def _std(windows: np.ndarray, axis: int) -> np.ndarray:
    return np.std(windows, axis=axis, ddof=1)


def _true_range(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> np.ndarray:
    previous = _shift(closes, 1)
    ranges = np.vstack(
        (highs - lows, np.abs(highs - previous), np.abs(lows - previous))
    )
    out = np.max(ranges, axis=0)
    out[0] = np.nan  # the first bar has no previous close
    return out


def _ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        out = numerator / denominator
    out[~np.isfinite(out)] = np.nan
    return out


def _beta_residual(
    returns: np.ndarray, market: np.ndarray, window: int
) -> tuple[np.ndarray, np.ndarray]:
    """The trailing OLS beta on the market, and the residuals' standard deviation."""
    beta = np.full(returns.shape, np.nan)
    residual = np.full(returns.shape, np.nan)
    if len(returns) < window:
        return beta, residual
    y = sliding_window_view(returns, window)
    x = sliding_window_view(market, window)
    xc = x - x.mean(axis=1, keepdims=True)
    yc = y - y.mean(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        slope = (xc * yc).sum(axis=1) / (xc * xc).sum(axis=1)
    spread = np.std(yc - slope[:, None] * xc, axis=1, ddof=1)
    beta[window - 1 :] = slope
    residual[window - 1 :] = spread
    beta[~np.isfinite(beta)] = np.nan
    residual[~np.isfinite(beta)] = np.nan
    return beta, residual
