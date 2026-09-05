"""Verdict-quality gate tests.

Agent: tooling
Role: prove the gate warns rather than blocks on its first day, and refuses to
      rule at all on a sample too small to carry a claim.
External I/O: none.
"""

from __future__ import annotations

from orchestration.agreement import Agreement
from orchestration.quality_gate import (
    GATE_FAIL,
    GATE_INSUFFICIENT,
    GATE_OK,
    GATE_WARN,
    evaluate_quality,
)
from orchestration.settings import DeliberationQualitySettings


def _judge(matched: int, compared: int, **kwargs: object) -> object:
    return evaluate_quality(
        Agreement("self_agreement", matched, compared, excluded=0),
        floor=kwargs.pop("floor", 0.56),  # type: ignore[arg-type]
        min_compared=kwargs.pop("min_compared", 10),  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def test_agreement_at_or_above_the_floor_passes() -> None:
    """The floor is a floor, so meeting it exactly is not a failure."""
    assert _judge(56, 100).status == GATE_OK


def test_agreement_below_the_floor_only_warns_on_its_first_day() -> None:
    """S156's pattern: an uncalibrated threshold must not block anything."""
    verdict = _judge(40, 100)

    assert verdict.status == GATE_WARN
    assert verdict.exit_code == 0


def test_the_same_shortfall_blocks_once_the_gate_is_armed() -> None:
    """The gate has teeth to grow into; --blocking is what grows them."""
    verdict = _judge(40, 100, warn_only=False)

    assert verdict.status == GATE_FAIL
    assert verdict.exit_code == 1


def test_too_few_pairs_makes_no_quality_claim_in_either_direction() -> None:
    """A 1-of-1 above the floor is not evidence of quality; it is one coin toss."""
    verdict = _judge(1, 1)

    assert verdict.status == GATE_INSUFFICIENT
    assert verdict.exit_code == 0
    assert "no quality claim is made either way" in verdict.render()


def test_nothing_compared_is_insufficient_rather_than_a_zero_percent_failure() -> None:
    """An empty sweep must not be reported as a total collapse in quality."""
    assert _judge(0, 0).status == GATE_INSUFFICIENT


def test_the_rendered_report_states_the_floor_and_the_mode_it_ran_in() -> None:
    """A status nobody can reproduce is not evidence."""
    rendered = _judge(56, 100).render()

    assert "floor\t56.00%" in rendered
    assert "mode\twarn-only" in rendered
    assert "compared=100" in rendered


def test_the_floor_default_is_the_only_figure_ever_measured() -> None:
    """DL-104's 9 of 16; the default must not be an invented round number."""
    settings = DeliberationQualitySettings()

    assert settings.self_agreement_floor == 0.56
    assert settings.min_compared_pairs == 10
