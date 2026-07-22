"""Alpha158 cross-sectional pillar scoring tests.

Agent: analyst
Role: verify score_alpha158 maps single-element universes to 50 and scores
      relative to the universe correctly.
External I/O: none.
"""

from __future__ import annotations

import dataclasses

import pytest

from agents.analyst.domain.alpha_features import AlphaFeatureRow
from agents.analyst.domain.alpha_pillar import score_alpha158

_FIELDS = [f.name for f in dataclasses.fields(AlphaFeatureRow)]


def _row(**overrides: float) -> AlphaFeatureRow:
    """Build an AlphaFeatureRow with all fields set to 0.5 unless overridden."""
    values = dict.fromkeys(_FIELDS, 0.5)
    values.update(overrides)
    return AlphaFeatureRow(**values)


def _high_row() -> AlphaFeatureRow:
    return AlphaFeatureRow(**dict.fromkeys(_FIELDS, 1.0))


def _low_row() -> AlphaFeatureRow:
    return AlphaFeatureRow(**dict.fromkeys(_FIELDS, 0.0))


def test_single_element_universe_returns_fifty() -> None:
    row = _row()
    assert score_alpha158(row, (row,)) == pytest.approx(50.0)


def test_dominating_row_scores_above_fifty() -> None:
    """Kills agents.analyst.domain.alpha_pillar.x_score_alpha158__mutmut_16."""
    high = _high_row()
    low = _low_row()
    assert score_alpha158(high, (high, low)) == pytest.approx(73.10585786300048)


def test_dominated_row_scores_below_fifty() -> None:
    """Kills agents.analyst.domain.alpha_pillar.x_score_alpha158__mutmut_19."""
    high = _high_row()
    low = _low_row()
    assert score_alpha158(low, (high, low)) == pytest.approx(26.894142136999513)


def test_scores_are_symmetric_around_fifty() -> None:
    high = _high_row()
    low = _low_row()
    score_h = score_alpha158(high, (high, low))
    score_l = score_alpha158(low, (high, low))
    assert score_h + score_l == pytest.approx(100.0)


def test_score_is_in_zero_to_hundred() -> None:
    high = _high_row()
    low = _low_row()
    for row in (high, low, _row()):
        s = score_alpha158(row, (high, low, _row()))
        assert 0.0 <= s <= 100.0


def test_feature_not_in_universe_is_appended_and_scored() -> None:
    """Kills agents.analyst.domain.alpha_pillar.x_score_alpha158__mutmut_28."""
    low = _low_row()
    outsider = _high_row()
    # outsider is NOT in the universe; it should be appended and get a high score
    assert score_alpha158(outsider, (low,)) == pytest.approx(73.10585786300048)


def test_exact_epsilon_std_feature_contributes_zero_z() -> None:
    """Kills agents.analyst.domain.alpha_pillar.x_score_alpha158__mutmut_28."""
    low = _row(roc_5=0.0)
    edge = _row(roc_5=2e-9)

    assert score_alpha158(edge, (edge, low)) == pytest.approx(50.0)


def test_zero_variance_feature_contributes_zero_z() -> None:
    # All rows identical → std = 0 for every field → z = 0 → score = 50
    row = _row()
    identical = (row, row, row)
    assert score_alpha158(row, identical) == pytest.approx(50.0)


def test_score_is_finite_for_extreme_values() -> None:
    """Kills agents.analyst.domain.alpha_pillar.x_score_alpha158__mutmut_33."""
    high = AlphaFeatureRow(**dict.fromkeys(_FIELDS, 10000000000.0))
    low = AlphaFeatureRow(**dict.fromkeys(_FIELDS, -10000000000.0))
    assert score_alpha158(high, (high, low)) == pytest.approx(73.10585786300048)
