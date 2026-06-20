"""Researcher proposal-builder tests.

Agent: researcher
Role: verify bounded confidence-floor proposal rules.
External I/O: none.
"""

from __future__ import annotations

from agents.researcher.domain.evidence import RunEvidence
from agents.researcher.domain.proposal import build_proposal
from agents.researcher.settings import ResearcherSettings


def test_low_confidence_raises_floor() -> None:
    """RES-NEV-03 / RES-TYP-02: low confidence → bounded floor raise."""
    proposal = build_proposal(_evidence(0.35), ResearcherSettings(), "raise")

    assert len(proposal.changes) == 1
    change = proposal.changes[0]
    assert change.parameter == "analyst.confidence_floor"
    assert change.current_value == 0.30
    assert change.proposed_value == 0.35
    assert change.evidence_window_days == 90
    assert "raise" in proposal.rationale.summary


def test_neutral_confidence_returns_zero_change() -> None:
    proposal = build_proposal(_evidence(0.50), ResearcherSettings(), "neutral")

    assert not proposal.changes
    assert "does not yet warrant" in proposal.rationale.summary


def test_high_confidence_lowers_floor() -> None:
    proposal = build_proposal(_evidence(0.75), ResearcherSettings(), "lower")

    assert proposal.changes[0].proposed_value == 0.25
    assert "Broader candidate flow" in proposal.changes[0].expected_effect.summary


def test_bound_and_window_violations_return_zero_change() -> None:
    """RES-NEV-03 / RES-NEV-02: at-bound or too-short window → zero change."""
    at_bound = ResearcherSettings(confidence_floor_reference=0.0)
    too_short = ResearcherSettings(lookback_days=30, min_evidence_window_days=31)

    bound_proposal = build_proposal(_evidence(0.75), at_bound, "bound")
    short_proposal = build_proposal(_evidence(0.35), too_short, "short")

    assert not bound_proposal.changes
    assert "safe bound" in bound_proposal.rationale.summary
    assert not short_proposal.changes
    assert "too short" in short_proposal.rationale.summary


def _evidence(confidence: float) -> RunEvidence:
    return RunEvidence(
        snapshot_count=5,
        avg_confidence=confidence,
        avg_approval_rate=0.80,
        avg_rejection_count=1.0,
    )
