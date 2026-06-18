"""Pure statistics for the sentiment champion-challenger scorecard.

Agent: forecaster
Role: deterministic Pearson correlation and 2-regressor OLS over aligned series.
External I/O: none.
"""

from __future__ import annotations


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def std(xs: list[float]) -> float:
    """Population standard deviation of a non-empty series."""
    mean = _mean(xs)
    return float((sum((x - mean) ** 2 for x in xs) / len(xs)) ** 0.5)


def pearson(xs: list[float], ys: list[float]) -> float | None:
    """Pearson correlation of two equal-length series.

    Returns ``None`` when there are fewer than two points or either series is
    constant (zero variance) -- the correlation is undefined, not zero. Never
    raises.
    """
    n = len(xs)
    if n < 2:
        return None
    mx, my = _mean(xs), _mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0.0 or syy == 0.0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    return float(sxy / (sxx**0.5 * syy**0.5))


def ols2(
    f: list[float], a: list[float], b: list[float]
) -> tuple[float, float, float, list[float]] | None:
    """Ordinary least squares ``f = alpha + beta*a + gamma*b``.

    Returns ``(alpha, beta, gamma, residuals)``, or ``None`` when there are fewer
    than three points or the two regressors are collinear (singular design).
    Solved in closed form on the centred series. Never raises.
    """
    n = len(f)
    if n < 3:
        return None
    mf, ma, mb = _mean(f), _mean(a), _mean(b)
    ca = [x - ma for x in a]
    cb = [x - mb for x in b]
    cf = [x - mf for x in f]
    saa = sum(x * x for x in ca)
    sbb = sum(x * x for x in cb)
    sab = sum(x * y for x, y in zip(ca, cb, strict=True))
    saf = sum(x * y for x, y in zip(ca, cf, strict=True))
    sbf = sum(x * y for x, y in zip(cb, cf, strict=True))
    det = saa * sbb - sab * sab
    if det == 0.0:
        return None
    beta = (saf * sbb - sbf * sab) / det
    gamma = (sbf * saa - saf * sab) / det
    alpha = mf - beta * ma - gamma * mb
    residuals = [
        fi - (alpha + beta * ai + gamma * bi)
        for fi, ai, bi in zip(f, a, b, strict=True)
    ]
    return alpha, beta, gamma, residuals
