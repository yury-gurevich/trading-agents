"""S255's first-failure guards and unrounded reproduction boundary.

Agent: deliberator
Role: prove incomplete or contradictory records produce one withheld line.
External I/O: local fixture reads only.
"""

from __future__ import annotations

import pytest
from tests.score_arithmetic_support import packet, recorded_order

from agents.deliberator.context_arithmetic import arithmetic_lines
from contracts.analyst import QuantMetric

REASONS = {
    "regime": "no regime record",
    "thresholds": "the regime record carries no label thresholds",
    "alpha": "the alpha158 pillar is active",
    "empty": "the recorded sub-scores are incomplete",
    "technical": "the recorded sub-scores are incomplete",
    "fundamental": "the recorded sub-scores are incomplete",
    "rs": "this order has no rs_score",
    "confidence": "the stated rule does not reproduce the recorded confidence_score",
    "blended": "the stated rule does not reproduce the recorded confidence_score",
    "zero_weights": "the stated rule does not reproduce the recorded confidence_score",
}


@pytest.mark.parametrize("broken", REASONS)
def test_each_failed_condition_withholds_one_line(broken: str) -> None:
    """DLIB-OUT-08 / DLIB-NEV-09: D4 never states an unreproduced rule."""
    rec, regime = recorded_order()
    sa = rec.score_arithmetic
    assert sa is not None
    if broken == "regime":
        regime = None
    elif broken == "thresholds":
        regime = regime.model_copy(update={"vix_thresholds": None})
    elif broken == "alpha":
        rec = rec.model_copy(
            update={
                "quant_metrics": (
                    *rec.quant_metrics,
                    QuantMetric(name="alpha158_score", value=50),
                ),
            }
        )
    elif broken == "empty":
        rec = rec.model_copy(
            update={
                "score_arithmetic": sa.model_copy(update={"technical_sub_scores": ()}),
            }
        )
    elif broken in {"technical", "fundamental", "rs"}:
        name = {
            "technical": sa.technical_sub_scores[0],
            "fundamental": sa.fundamental_sub_scores[0],
            "rs": "rs_score",
        }[broken]
        rec = rec.model_copy(
            update={
                "quant_metrics": tuple(m for m in rec.quant_metrics if m.name != name),
            }
        )
    elif broken in {"confidence", "blended"}:
        name = "confidence" if broken == "confidence" else "technical_score"
        rec = rec.model_copy(update={name: getattr(rec, name) + 2e-9})
    else:
        rec = rec.model_copy(
            update={
                "score_arithmetic": sa.model_copy(
                    update={
                        "technical_weight": 0.0,
                        "fundamental_weight": 0.0,
                        "sentiment_weight": 0.0,
                    }
                )
            }
        )
    expected = f"Score arithmetic: withheld; {REASONS[broken]}."
    assert arithmetic_lines(rec, regime, rec.ticker) == [expected]
    assert packet(rec, regime).splitlines()[-1] == expected


def test_first_failed_condition_wins_and_old_records_add_nothing() -> None:
    """DLIB-OUT-08: D4 checks in order and makes no demand on old records."""
    rec, regime = recorded_order()
    assert arithmetic_lines(None, None, rec.ticker) == []
    assert (
        arithmetic_lines(
            rec.model_copy(update={"score_arithmetic": None}), None, rec.ticker
        )
        == []
    )
    broken = rec.model_copy(
        update={
            "quant_metrics": (QuantMetric(name="alpha158_score", value=50),),
        }
    )
    assert arithmetic_lines(broken, None, rec.ticker) == [
        "Score arithmetic: withheld; no regime record.",
    ]
    assert arithmetic_lines(
        broken, regime.model_copy(update={"vix_thresholds": None}), rec.ticker
    ) == [
        "Score arithmetic: withheld; the regime record carries no label thresholds.",
    ]
    assert arithmetic_lines(broken, regime, rec.ticker) == [
        "Score arithmetic: withheld; the alpha158 pillar is active.",
    ]
    assert arithmetic_lines(
        rec.model_copy(update={"quant_metrics": ()}), regime, rec.ticker
    ) == [
        "Score arithmetic: withheld; the recorded sub-scores are incomplete.",
    ]


@pytest.mark.parametrize("field", ["confidence", "technical_score"])
def test_small_unrounded_differences_are_within_the_tolerance(field: str) -> None:
    """DLIB-OUT-08 / DLIB-NEV-09: D5 uses 1e-9, not rounded text or exact equality."""
    rec, regime = recorded_order()
    rec = rec.model_copy(update={field: getattr(rec, field) + 0.5e-9})
    assert len(arithmetic_lines(rec, regime, rec.ticker)) == 3


@pytest.mark.parametrize("missing", ["scan", "market"])
def test_partial_lineage_withholds_without_moving_existing_lines(missing: str) -> None:
    """DLIB-OUT-08 / DLIB-OUT-07: missing upstream lineage still states its reason."""
    rec, regime = recorded_order()
    old = packet(
        rec.model_copy(update={"score_arithmetic": None}), regime, missing=missing
    )
    assert (
        packet(rec, regime, missing=missing)
        == old + "\nScore arithmetic: withheld; no regime record."
    )
