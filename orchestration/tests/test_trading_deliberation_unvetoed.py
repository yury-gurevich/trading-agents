"""A run whose veto could not execute at all does not stay green.

Agent: orchestration
Role: prove both routes to an unexecuted veto breach — no `DeliberationRun`, and a
      `DeliberationRun` every one of whose subjects failed open — while a veto that
      degraded on *some* subjects stays green with its stated reason.
External I/O: none.

Operator decision, 2026-09-13 — *"should a run where the veto could not execute at
all stay green under advisory posture? No."*

🪤 **The line is partial-vs-total, not present-vs-absent.** Keying only on the
absent-`DeliberationRun` statuses produced a rule that could never fire. Measured
over the 40 linked `ExecutionRun` rows carrying a deliberation status, 2026-09-13:

| Condition | Occurrences |
| --- | --- |
| `advisory` + `proceeded_unvetoed` | **0** |
| `advisory` + `applied_failed_open`, `failed_open_count == reviewed` | **4** |
| `advisory` + `applied_failed_open`, `0 < failed_open_count < reviewed` | **0** |

All four of the second row carry `real_debate_count=0` and a `failed_open_reason`
naming `400 … credit balance is too low` — the 2026-08-21→28 and 2026-09-08→11
billing outages, i.e. precisely the incident this sprint exists for. A rule that
skipped them would have been a tripwire for a condition that has never happened.

🪤 **[DL-125](../../docs/design-log.md) does not protect that row.** It argued
against nightly red *for a declared, accepted, external outage*, proposing the
declared `advisory` posture so knowingly-unvetoed submissions get "a stated mode
with a truthful green" — and its own `sched-2026-08-21` record treats that run
failing acceptance as correct. Declared posture excuses trading unvetoed; it does
not excuse reporting that the veto worked. What stays green is the third row: a
veto that ran and degraded on some of its subjects, which is a different fact and
has its own recorded cause.
"""

from __future__ import annotations

import pytest

from orchestration.observatory import breaches
from orchestration.packs.trading_deliberation_view import deliberation
from orchestration.tests.test_trading_deliberation_not_required import (
    _deliberation_graph,
)

CREDIT_400 = (
    "RuntimeError: Error code: 400 - {'type': 'error', 'error': "
    "{'type': 'invalid_request_error', 'message': 'Your credit balance is too low'}}"
)


def test_unvetoed_advisory_buy_breaches() -> None:
    """🎯 EXEC-OUT-09 / EXEC-OBS-04: no DeliberationRun at all, with a buy out."""
    graph, node = _deliberation_graph("buy", status="proceeded_unvetoed")

    view = deliberation(graph, node)

    assert view.observed["advisory_attribution"] == "veto_never_ran"
    assert any(breach.key == "advisory_attribution" for breach in breaches(view))


def test_unvetoed_advisory_sell_only_run_stays_green() -> None:
    """No buy reached the broker unreviewed, so there is nothing to be red about.

    The gate only produces `proceeded_unvetoed` when the approved set contains a
    buy, so this is a defensive branch — but it keeps the rule about *unreviewed
    exposure* rather than about a status string.
    """
    graph, node = _deliberation_graph("sell", status="proceeded_unvetoed")

    view = deliberation(graph, node)

    assert view.observed["advisory_attribution"] == "ok"
    assert breaches(view) == ()


def test_unvetoed_advisory_with_unreadable_pm_payload_breaches() -> None:
    """An unreadable approved set cannot prove no buy escaped review."""
    graph, node = _deliberation_graph(
        status="proceeded_unvetoed", order_payload={"approved": "not-contract"}
    )

    view = deliberation(graph, node)

    assert view.observed["advisory_attribution"] == "veto_never_ran"
    assert any(breach.key == "advisory_attribution" for breach in breaches(view))


@pytest.mark.parametrize("subjects", [("AAPL",), ("AAPL", "MSFT"), ("A", "B", "C")])
def test_a_veto_that_reviewed_nothing_breaches(subjects: tuple[str, ...]) -> None:
    """🎯 The measured incident: a DeliberationRun exists and reviewed none of them.

    This is the shape all four real occurrences take — `real_debate_count=0`, every
    subject failed open, a `400 ... credit balance is too low` reason recorded, and
    before S202 an `advisory_attribution` of `ok`.
    """
    graph, node = _deliberation_graph(
        "buy",
        status="applied_failed_open",
        failed_open_count=len(subjects),
        failed_open_reason=CREDIT_400,
        reviewed_tickers=subjects,
    )

    view = deliberation(graph, node)

    assert view.observed["advisory_attribution"] == "veto_never_ran"
    assert any(breach.key == "advisory_attribution" for breach in breaches(view))


@pytest.mark.parametrize(
    ("subjects", "failed"),
    [(("AAPL", "MSFT"), 1), (("A", "B", "C"), 1), (("A", "B", "C"), 2)],
)
def test_a_partially_degraded_veto_stays_green(
    subjects: tuple[str, ...], failed: int
) -> None:
    """🪤 The case DL-125 actually protects: the veto ran and reviewed some of them.

    It has occurred **0** times on the live spine, which is worth stating — this is
    the theoretical branch, and the one that looked like the common case from the
    status label alone.
    """
    graph, node = _deliberation_graph(
        "buy",
        status="applied_failed_open",
        failed_open_count=failed,
        failed_open_reason="RuntimeError: provider timeout on one subject",
        reviewed_tickers=subjects,
    )

    view = deliberation(graph, node)

    assert view.observed["advisory_attribution"] == "ok"
    assert breaches(view) == ()


def test_a_fail_open_without_a_reason_is_still_unattributed() -> None:
    """The pre-existing rule survives: a fail-open must name its own cause."""
    graph, node = _deliberation_graph(
        "buy",
        status="applied_failed_open",
        failed_open_count=1,
        failed_open_reason="",
        reviewed_tickers=("AAPL", "MSFT"),
    )

    view = deliberation(graph, node)

    assert view.observed["advisory_attribution"] == "missing"
    assert any(breach.key == "advisory_attribution" for breach in breaches(view))


def test_a_clean_applied_veto_stays_green() -> None:
    """A veto that ran with no fail-opens is unaffected by any of this."""
    graph, node = _deliberation_graph(
        "buy", status="applied", reviewed_tickers=("AAPL", "MSFT")
    )

    view = deliberation(graph, node)

    assert view.observed["advisory_attribution"] == "ok"
    assert breaches(view) == ()


def test_binding_posture_is_untouched_by_the_advisory_rule() -> None:
    """Binding already drops the buys outright; its checks are unchanged."""
    graph, node = _deliberation_graph(
        "buy", posture="binding", status="proceeded_unvetoed"
    )

    found = breaches(deliberation(graph, node))

    assert "advisory_attribution" not in {breach.key for breach in found}
