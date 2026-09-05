"""Verdict agreement metric tests.

Agent: tooling
Role: prove a fail-open can never be counted as agreement, and that the
      denominator is the number of comparable pairs and nothing else.
External I/O: none.
"""

from __future__ import annotations

from orchestration.verdict_metrics import (
    ReplayVerdict,
    agreement_with,
    self_agreement,
)


def _replay(
    ticker: str = "USB",
    ruling: str | None = "uphold",
    repeat: int = 1,
    arm: str = "control",
    failure: str | None = None,
) -> ReplayVerdict:
    return ReplayVerdict(
        pm_run="pm-run-1",
        ticker=ticker,
        arm=arm,
        repeat=repeat,
        ruling=ruling,
        failure=failure,
    )


def test_repeats_of_one_decision_are_compared_pairwise() -> None:
    """Three repeats give three pairs, not three comparisons against a first."""
    measured = self_agreement(
        [
            _replay(repeat=n, ruling=r)
            for n, r in enumerate(("uphold", "uphold", "revise"), 1)
        ]
    )

    assert (measured.matched, measured.compared) == (1, 3)


def test_two_different_decisions_are_never_compared_against_each_other() -> None:
    """Agreement is about one decision replayed twice, not about two decisions."""
    measured = self_agreement([_replay("USB"), _replay("AVGO", ruling="revise")])

    assert measured.compared == 0
    assert measured.rate is None


def test_a_failed_replay_is_excluded_and_counted_not_treated_as_a_verdict() -> None:
    """DL-104's run D is 5 of 6, not 5 of 10 — this is that predicate."""
    measured = self_agreement(
        [_replay(repeat=1), _replay(repeat=2), _replay(repeat=3, failure="expired")]
    )

    assert (measured.matched, measured.compared, measured.excluded) == (1, 1, 1)


def test_a_verdictless_record_is_excluded_even_without_a_named_failure() -> None:
    """A null ruling is not an 'uphold'; it is an absence."""
    measured = self_agreement([_replay(repeat=1), _replay(repeat=2, ruling=None)])

    assert (measured.compared, measured.excluded) == (0, 1)


def test_one_arm_can_be_measured_without_the_others_contaminating_it() -> None:
    """The sweep's whole point is comparing arms, so arms must not pool."""
    verdicts = [
        _replay(repeat=1, arm="control"),
        _replay(repeat=2, arm="control"),
        _replay(repeat=1, arm="effort", ruling="revise"),
        _replay(repeat=2, arm="effort", ruling="uphold"),
    ]

    assert self_agreement(verdicts, arm="control").matched == 1
    assert self_agreement(verdicts, arm="effort").matched == 0
    assert "self_agreement[effort]" in self_agreement(verdicts, arm="effort").detail()


def test_agreement_with_a_second_source_reports_what_it_could_not_compare() -> None:
    """A decision the other source never ruled on is absent, not a disagreement."""
    measured = agreement_with(
        [_replay("USB", "revise"), _replay("AVGO", "uphold"), _replay("C", "uphold")],
        {("pm-run-1", "USB"): "revise", ("pm-run-1", "AVGO"): "revise"},
        name="agreement_with_recorded_verdict",
    )

    assert (measured.matched, measured.compared) == (1, 2)
    assert measured.no_counterpart == 1
    assert measured.excluded == 0


def test_the_second_source_comparison_excludes_failed_replays_too() -> None:
    """The exclusion predicate is defined once and applies to every metric."""
    measured = agreement_with(
        [_replay("USB", None, failure="errored")],
        {("pm-run-1", "USB"): "revise"},
        name="cross",
        arm="control",
    )

    assert (measured.compared, measured.excluded) == (0, 1)
    assert measured.name == "cross[control]"
