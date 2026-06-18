"""Sentiment champion-challenger scorecard math.

Agent: forecaster
Role: turn aligned (lexicon, provider, finbert, forward-return) observations into
      the comparison metrics -- pairwise correlations, each scorer's information
      coefficient on forward returns, the OLS of finbert on the other two, and
      finbert's incremental information coefficient (its residual's IC).
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass

from agents.forecaster.domain.statistics import ols2, pearson, std


@dataclass(frozen=True)
class Observation:
    """One aligned complete case: each scorer's 0-1 score + the forward return."""

    ref: str
    lexicon: float
    provider: float
    finbert: float
    forward_return: float


def _put(metrics: dict[str, float], key: str, value: float | None) -> None:
    """Record a metric only when it is defined, so a present key is meaningful."""
    if value is not None:
        metrics[key] = value


def comparison_metrics(observations: list[Observation]) -> dict[str, float]:
    """Comparison metrics over complete-case observations; never raises.

    Empty when there are no observations. Each metric is omitted when undefined
    (fewer than two/three points, a constant series, or collinear regressors).
    """
    metrics: dict[str, float] = {}
    if not observations:
        return metrics
    metrics["complete_cases"] = float(len(observations))
    lex = [o.lexicon for o in observations]
    prov = [o.provider for o in observations]
    fin = [o.finbert for o in observations]
    ret = [o.forward_return for o in observations]
    _put(metrics, "corr_lexicon_provider", pearson(lex, prov))
    _put(metrics, "corr_lexicon_finbert", pearson(lex, fin))
    _put(metrics, "corr_provider_finbert", pearson(prov, fin))
    _put(metrics, "ic_lexicon", pearson(lex, ret))
    _put(metrics, "ic_provider", pearson(prov, ret))
    _put(metrics, "ic_finbert", pearson(fin, ret))
    _add_regression(metrics, fin=fin, prov=prov, lex=lex, ret=ret)
    return metrics


def _add_regression(
    metrics: dict[str, float],
    *,
    fin: list[float],
    prov: list[float],
    lex: list[float],
    ret: list[float],
) -> None:
    """OLS finbert = a + b*provider + g*lexicon; residual std + incremental IC."""
    fit = ols2(fin, prov, lex)
    if fit is None:
        return
    alpha, beta, gamma, residuals = fit
    metrics["finbert_alpha"] = alpha
    metrics["finbert_beta_provider"] = beta
    metrics["finbert_beta_lexicon"] = gamma
    metrics["finbert_residual_std"] = std(residuals)
    _put(metrics, "incremental_ic_finbert", pearson(residuals, ret))
