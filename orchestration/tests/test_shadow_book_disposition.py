"""Shadow-book recorded-disposition tests.

Agent: orchestration
Role: prove PM history is classified without re-running portfolio logic.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from kernel import InMemoryGraphStore
from orchestration.shadow_book import ShadowOutcome, derive_shadow_book
from orchestration.tests.shadow_book_helpers import bar, recommendation, seed_run

AS_OF = date(2026, 8, 3)
NEXT_DAY = date(2026, 8, 4)


def test_c1_max_positions_is_blocked_capacity() -> None:
    """S160-C1: the recorded max_positions reason drives the key bucket."""
    outcome = _disposition_outcome(rejected=(("MSFT", "max_positions"),))
    assert (outcome.disposition, outcome.disposition_reason) == (
        "blocked_capacity",
        "max_positions",
    )


def test_c2_other_rejection_is_blocked_other_with_reason() -> None:
    """S160-C2: hold_recommendation is not miscounted as capacity."""
    outcome = _disposition_outcome(rejected=(("MSFT", "hold_recommendation"),))
    assert (outcome.disposition, outcome.disposition_reason) == (
        "blocked_other",
        "hold_recommendation",
    )


def test_c3_approved_recommendation_is_taken() -> None:
    """S160-C3: a recorded approved intent is classified as taken."""
    outcome = _disposition_outcome(approved=("MSFT",))
    assert (outcome.disposition, outcome.disposition_reason) == ("taken", None)


def test_c4_recorded_reason_wins_over_current_context() -> None:
    """S160-C4: a planted historical rejection is read, never re-derived."""
    outcome = _disposition_outcome(rejected=(("MSFT", "max_positions"),))
    assert outcome.disposition == "blocked_capacity"


def test_unmatched_or_absent_pm_decision_is_not_actionable() -> None:
    """A recommendation absent from recorded PM candidates remains explicit."""
    with_pm = _disposition_outcome(rejected=(("AAPL", "some_reason"),))
    no_pm = _disposition_outcome(include_pm=False)
    assert with_pm.disposition == "not_actionable"
    assert no_pm.disposition == "not_actionable"


def _disposition_outcome(
    *,
    approved: tuple[str, ...] = (),
    rejected: tuple[tuple[str, str], ...] = (),
    include_pm: bool = True,
) -> ShadowOutcome:
    graph = InMemoryGraphStore()
    seed_run(
        graph,
        "analyst-c",
        AS_OF,
        (recommendation("MSFT"),),
        (bar("MSFT", AS_OF, 100.0), bar("MSFT", NEXT_DAY, 110.0)),
        approved=approved,
        rejected=rejected,
        include_pm=include_pm,
    )
    return derive_shadow_book(graph, (1,))[0]
