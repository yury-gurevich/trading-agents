"""Deliberation understanding scorer + trading answer-key tests.

Agent: kernel
Role: verify the scorer grades parameter definitions (cited / understood / misread),
      that a known misread dominates a correct marker, that the rate is over cited
      params only, and that every trading answer-key entry is a real settings field.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.settings import AnalystSettings
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider.settings import ProviderSettings
from kernel import (
    ParameterTruth,
    misread_parameters,
    score_understanding,
    understanding_rate,
)
from orchestration.packs.trading_parameter_truths import TRADING_PARAMETER_TRUTHS

_TRUTHS = (
    ParameterTruth(
        name="max_daily_move_sigma",
        correct_markers=("pooled", "cross-sectional"),
        misread_markers=("per-stock", "that stock's"),
    ),
)


def test_correct_definition_is_understood() -> None:
    text = "max_daily_move_sigma = a pooled cross-sectional gate across the batch."
    (score,) = score_understanding(text, _TRUTHS)
    assert score.cited
    assert score.understood
    assert not score.misread


def test_known_misread_dominates_even_with_a_correct_marker() -> None:
    """A misread marker counts as misread even if a correct marker also appears."""
    text = "max_daily_move_sigma = pooled, but really it's that stock's own vol."
    (score,) = score_understanding(text, _TRUTHS)
    assert score.cited
    assert score.misread
    assert not score.understood


def test_uncited_parameter_scores_not_cited() -> None:
    (score,) = score_understanding("nothing about it here", _TRUTHS)
    assert not score.cited
    assert not score.understood
    assert not score.misread


def test_misread_marker_without_citation_is_not_a_misread() -> None:
    """A marker word elsewhere in the debate is not a reading of an un-cited param
    (the false-positive the first live run surfaced)."""
    truths = (
        ParameterTruth(
            "signal_diversity_slack",
            correct_markers=("unused pillar",),
            misread_markers=("correlation",),
        ),
    )
    (score,) = score_understanding("AMD has high correlation w/ Nasdaq", truths)
    assert not score.cited
    assert not score.misread


def test_understanding_rate_is_over_cited_only() -> None:
    truths = (
        _TRUTHS[0],
        ParameterTruth("other_param", correct_markers=("ok",), misread_markers=()),
    )
    # only max_daily_move_sigma is cited, and it is understood -> 1.0
    text = "max_daily_move_sigma = pooled cross-sectional"
    assert understanding_rate(score_understanding(text, truths)) == 1.0


def test_understanding_rate_zero_when_nothing_cited() -> None:
    assert understanding_rate(score_understanding("", _TRUTHS)) == 0.0


def test_misread_parameters_lists_the_wrong_reads() -> None:
    text = "max_daily_move_sigma = that stock's volatility filter"
    assert misread_parameters(score_understanding(text, _TRUTHS)) == (
        "max_daily_move_sigma",
    )


def test_answer_key_entries_are_real_settings_fields() -> None:
    """Coverage: every trading truth names a live tunable, so the key cannot drift."""
    fields = (
        set(ProviderSettings.model_fields)
        | set(AnalystSettings.model_fields)
        | set(PortfolioManagerSettings.model_fields)
    )
    assert TRADING_PARAMETER_TRUTHS  # non-empty
    for truth in TRADING_PARAMETER_TRUTHS:
        assert truth.name in fields, truth.name
        assert truth.correct_markers
        assert truth.misread_markers
