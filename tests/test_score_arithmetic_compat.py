"""Backward-compatible records and the arithmetic module's recipe membership.

Agent: testing
Role: prove optional frozen records and scope of source-digest changes.
External I/O: local fixtures and one temporary source copy only.
"""

from __future__ import annotations

from pathlib import Path

import dspy
import pytest
from pydantic import ValidationError
from tests.score_arithmetic_support import recorded_order
from tests.veto_context_fixtures import recs

from agents.deliberator import context_arithmetic
from agents.deliberator import prompt_recipe as deliberator
from agents.operator import prompt_recipe as operator
from contracts.analyst import RecommendationSet, ScoreArithmetic
from contracts.provider import RegimeContext, VixThresholds
from kernel.prompt_recipe import recipe_digest


def test_old_and_new_recommendation_sets_and_regimes_validate() -> None:
    """ANLZ-OUT-10 / PROV-OUT-02 / DLIB-OUT-08: readers accept both record shapes."""
    rec, regime = recorded_order()
    old_set = recs()
    old_regime = regime.model_dump(mode="json", exclude={"vix_thresholds"})
    assert (
        RecommendationSet.model_validate(old_set).recommendations[0].score_arithmetic
        is None
    )
    assert RegimeContext.model_validate(old_regime).vix_thresholds is None
    new_set = {**old_set, "recommendations": [rec.model_dump(mode="json")]}
    parsed_set = RecommendationSet.model_validate(new_set)
    parsed_regime = RegimeContext.model_validate_json(regime.model_dump_json())
    assert parsed_set.recommendations[0] == rec
    assert parsed_regime == regime
    assert (
        RecommendationSet.model_validate_json(parsed_set.model_dump_json())
        == parsed_set
    )
    # _Frozen keeps its existing extra='ignore' behavior for future field readers.
    assert (
        RegimeContext.model_validate(
            {**old_regime, "future_field": {"unused": True}}
        ).vix_thresholds
        is None
    )


def test_arithmetic_and_threshold_records_are_frozen_and_finite() -> None:
    """ANLZ-OUT-10 / PROV-OUT-02: recorded constants cannot mutate or encode NaN."""
    rec, regime = recorded_order()
    sa, vix = rec.score_arithmetic, regime.vix_thresholds
    assert sa is not None
    assert vix is not None
    with pytest.raises(ValidationError, match="frozen_instance"):
        sa.confidence_floor = 0.0
    with pytest.raises(ValidationError, match="frozen_instance"):
        vix.risk_off_from = 0.0
    with pytest.raises(ValidationError, match="finite_number"):
        ScoreArithmetic.model_validate(
            {**sa.model_dump(), "confidence_span": float("nan")}
        )
    with pytest.raises(ValidationError, match="finite_number"):
        VixThresholds.model_validate(
            {**vix.model_dump(), "risk_off_from": float("inf")}
        )


def test_arithmetic_source_changes_only_the_deliberator_recipe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DLIB-OBS-07: the real recipe declares the renderer, the operator does not."""
    versions = {"dspy": dspy.__version__}
    before = recipe_digest(deliberator.PROMPT_MODULES, versions=versions)
    operator_before = recipe_digest(operator.PROMPT_MODULES)
    changed = tmp_path / "context_arithmetic.py"
    changed.write_bytes(
        Path(context_arithmetic.__file__).read_bytes()
        + b"\n# S255 planted source change\n"
    )
    monkeypatch.setattr(context_arithmetic, "__file__", str(changed))
    assert recipe_digest(deliberator.PROMPT_MODULES, versions=versions) != before
    assert recipe_digest(operator.PROMPT_MODULES) == operator_before
