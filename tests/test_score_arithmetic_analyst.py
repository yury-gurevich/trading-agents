"""Recorded analyst settings and the source-to-packet arithmetic pin.

Agent: testing
Role: compare real analyst rules with the deliberator's frozen formula.
External I/O: local fixture reads only.
"""

from __future__ import annotations

import pytest
from tests.score_arithmetic_analyst_support import (
    FUNDAMENTALS,
    bars,
    scored_order,
    settings,
)
from tests.score_arithmetic_support import recorded_order

from agents.analyst.domain.fundamental_rules import score_fundamental
from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import score_candidate
from agents.analyst.domain.technical_rules import score_technical
from agents.analyst.tests.helpers import candidate
from agents.deliberator.context_arithmetic import arithmetic_lines, recompute


@pytest.mark.parametrize("moved", [False, True])
def test_analyst_records_every_constant_and_the_actual_mean_order(moved: bool) -> None:
    """ANLZ-OUT-10: constants come from active settings, names from actual means."""
    config = settings(moved)
    score, rec = scored_order(config)
    sa = rec.score_arithmetic
    assert sa is not None
    assert sa == score.score_arithmetic
    for name in (
        "technical_weight",
        "fundamental_weight",
        "sentiment_weight",
        "relative_strength_weight",
        "confidence_floor",
        "confidence_span",
    ):
        assert getattr(sa, name) == getattr(config, name)
    assert sa.alpha158_weight == config.alpha158_pillar_weight
    raw_tech, tech = score_technical(list(bars()), config)
    raw_fund, fund = score_fundamental(FUNDAMENTALS)
    assert sa.technical_sub_scores == tuple(
        name for name in tech if name.endswith("_score")
    )
    assert sa.fundamental_sub_scores == (
        "pe",
        "roe",
        "net_margin",
        "current_ratio",
        "pb",
        "debt_equity",
        "eps_growth",
        "revenue_growth",
    )
    assert sa.fundamental_sub_scores == tuple(
        name for name in fund if name != "fundamentals_available"
    )
    assert (
        sum(tech[name] for name in sa.technical_sub_scores)
        / len(sa.technical_sub_scores)
        == raw_tech
    )
    assert (
        sum(fund[name] for name in sa.fundamental_sub_scores)
        / len(sa.fundamental_sub_scores)
        == raw_fund
    )
    assert {m.name: m.value for m in rec.quant_metrics} == score.metrics
    assert rec.confidence == score.confidence
    assert rec.technical_score == score.technical_score


@pytest.mark.parametrize("moved", [False, True])
@pytest.mark.parametrize("absent", ["none", "fundamental", "sentiment", "both"])
def test_the_packet_formula_reproduces_real_analyst_outputs(
    moved: bool, absent: str
) -> None:
    """DLIB-NEV-09 / ANLZ-OUT-10: present weights, means and affine mapping match."""
    config = settings(moved)
    score, rec = scored_order(config, absent)
    sa = rec.score_arithmetic
    assert sa is not None
    r = recompute(rec, sa)
    assert abs(r.confidence - score.confidence) <= 1e-9
    assert abs(r.present["technical"] - score.technical_score) <= 1e-9
    assert abs(r.composite - score.metrics["composite_score"]) <= 1e-9
    if absent in {"fundamental", "both"}:
        assert "fundamental" not in r.present
    if absent in {"sentiment", "both"}:
        assert "sentiment" not in r.present
    _, regime = recorded_order()
    lines = arithmetic_lines(rec, regime, rec.ticker)
    assert len(lines) == 3
    assert "withheld" not in "\n".join(lines)
    assert ("fundamental sub-scores (" in lines[1]) == ("fundamental" in r.present)
    assert ("; sentiment_score=" in lines[1]) == ("sentiment" in r.present)


@pytest.mark.parametrize(
    ("held", "stop_breached", "exit_floor", "action"),
    [
        (False, False, 0.0, "buy"),
        (True, False, 0.0, "hold"),
        (True, False, 1.0, "sell"),
        (True, True, 0.0, "sell"),
    ],
)
def test_each_recommendation_path_keeps_the_scored_arithmetic(
    held: bool,
    stop_breached: bool,
    exit_floor: float,
    action: str,
) -> None:
    """ANLZ-OUT-10 / ANLZ-IDM-01: buy, hold and both sell paths carry the same score."""
    config = settings()
    score, _ = scored_order(config)
    _, regime = recorded_order()
    regime = regime.model_copy(update={"base_min_confidence": 0.0})
    rec = decide(
        candidate(),
        score,
        regime,
        held=held,
        stop_breached=stop_breached,
        exit_confidence_floor=exit_floor,
        settings=config,
    ).recommendation
    assert rec is not None
    assert rec.action == action
    assert rec.score_arithmetic == score.score_arithmetic
    assert rec.confidence == score.confidence
    assert {m.name: m.value for m in rec.quant_metrics} == score.metrics


def test_a_stop_sale_with_short_history_records_constants_and_empty_means() -> None:
    """ANLZ-OUT-10: a short-history stop records constants and empty means."""
    config = settings(True)
    score = score_candidate(candidate(), bars()[:1], {}, (), (), config)
    _, regime = recorded_order()
    rec = decide(
        candidate(), score, regime, held=True, stop_breached=True, settings=config
    ).recommendation
    assert rec is not None
    assert rec.score_arithmetic is not None
    assert rec.quant_metrics
    assert rec.confidence == 0.0
    assert rec.score_arithmetic.technical_sub_scores == ()
    assert rec.score_arithmetic.fundamental_sub_scores == ()
    assert rec.score_arithmetic.confidence_floor == config.confidence_floor
