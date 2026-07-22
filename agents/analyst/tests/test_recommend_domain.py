"""Recommendation-domain payload contract tests.

Agent: analyst
Role: pin structured recommendation fields that are not operator prose.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import ScoreBreakdown
from agents.analyst.tests.helpers import candidate
from contracts.common import Provenance
from contracts.provider import RegimeContext


def _regime() -> RegimeContext:
    return RegimeContext(
        label="risk_on",
        vix=12.0,
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.30,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime-fixture", source_agent="provider"),
    )


def test_decide_emits_exact_recommendation_payload_contract() -> None:
    """Kills recommend.x_decide mutmut_34-39, 43, 50, 69, and 79."""
    score = ScoreBreakdown(
        technical_score=0.72,
        confidence=0.81,
        metrics={"zeta": 0.7, "alpha": 0.2},
        fundamental_score=0.64,
        sentiment_score=0.58,
        top_signals=("macd_histogram", "sentiment"),
    )

    decision = decide(candidate(), score, _regime())

    assert decision.rejection is None
    assert decision.recommendation is not None
    rec = decision.recommendation
    assert rec.action == "buy"
    assert rec.confidence == 0.81
    assert rec.technical_score == 0.72
    assert rec.fundamental_score == 0.64
    assert rec.sentiment_score == 0.58
    assert rec.suggested_stop_pct == 0.05
    assert rec.suggested_target_pct == 0.10
    assert rec.rationale.evidence_refs == (
        "analyst.technical_score",
        "provider.market_data",
        "provider.regime",
        "analyst.fundamental_score",
        "analyst.sentiment_score",
        "analyst.signal.macd_histogram",
        "analyst.signal.sentiment",
    )
    assert [(metric.name, metric.value) for metric in rec.quant_metrics] == [
        ("alpha", 0.2),
        ("zeta", 0.7),
    ]
