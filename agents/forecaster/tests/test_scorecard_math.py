"""Scorecard comparison-metric tests.

Agent: forecaster
Role: verify comparison_metrics over aligned observations, incl. omitted-when-
      undefined metrics and the regression / incremental-IC branches.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.domain.scorecard import Observation, comparison_metrics


def _obs(ref: str, lex: float, prov: float, fin: float, ret: float) -> Observation:
    return Observation(
        ref=ref, lexicon=lex, provider=prov, finbert=fin, forward_return=ret
    )


def test_no_observations_is_empty() -> None:
    assert comparison_metrics([]) == {}


def test_single_observation_only_counts_the_case() -> None:
    # n<2 makes every correlation undefined and n<3 makes the regression undefined.
    assert comparison_metrics([_obs("r:A", 0.5, 0.5, 0.5, 0.1)]) == {
        "complete_cases": 1.0
    }


def test_collinear_and_constant_legs_omit_their_metrics() -> None:
    # provider/lexicon collinear -> no regression; finbert constant -> no finbert
    # correlations or IC; the defined metrics are still present.
    obs = [
        _obs("r:A", 0.2, 0.1, 0.5, 0.1),
        _obs("r:B", 0.4, 0.2, 0.5, 0.2),
        _obs("r:C", 0.6, 0.3, 0.5, 0.3),
    ]
    metrics = comparison_metrics(obs)
    assert metrics["complete_cases"] == 3.0
    assert "corr_lexicon_provider" in metrics
    assert "ic_lexicon" in metrics
    assert "ic_provider" in metrics
    assert "corr_lexicon_finbert" not in metrics
    assert "ic_finbert" not in metrics
    assert "finbert_alpha" not in metrics  # singular design -> regression omitted


def test_constant_returns_omit_every_information_coefficient() -> None:
    # The regression still fits (finbert varies), but with zero return-variance
    # every IC -- and the incremental IC -- is undefined and omitted.
    obs = [
        _obs("r:A", 0.9, 0.1, 0.20, 0.02),
        _obs("r:B", 0.4, 0.5, 0.40, 0.02),
        _obs("r:C", 0.1, 0.9, 0.95, 0.02),
        _obs("r:D", 0.6, 0.3, 0.50, 0.02),
    ]
    metrics = comparison_metrics(obs)
    assert "finbert_beta_provider" in metrics
    assert metrics["finbert_residual_std"] >= 0.0
    assert "ic_lexicon" not in metrics
    assert "ic_finbert" not in metrics
    assert "incremental_ic_finbert" not in metrics
    assert "corr_lexicon_provider" in metrics  # scorer series still vary


def test_full_case_reports_regression_and_incremental_ic() -> None:
    obs = [
        _obs("r:A", 0.9, 0.1, 0.20, 0.05),
        _obs("r:B", 0.5, 0.5, 0.40, -0.02),
        _obs("r:C", 0.1, 0.9, 0.95, 0.08),
        _obs("r:D", 0.7, 0.3, 0.50, 0.01),
    ]
    metrics = comparison_metrics(obs)
    for key in (
        "corr_lexicon_provider",
        "corr_lexicon_finbert",
        "corr_provider_finbert",
        "ic_lexicon",
        "ic_provider",
        "ic_finbert",
        "finbert_alpha",
        "finbert_beta_provider",
        "finbert_beta_lexicon",
        "finbert_residual_std",
        "incremental_ic_finbert",
    ):
        assert key in metrics
    assert metrics["finbert_residual_std"] >= 0.0
    assert -1.0 <= metrics["incremental_ic_finbert"] <= 1.0
