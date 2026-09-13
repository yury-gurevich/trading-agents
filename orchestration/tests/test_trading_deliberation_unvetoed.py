"""A run whose veto could not execute at all does not stay green.

Agent: orchestration
Role: prove `advisory` + `proceeded_unvetoed` with approved buys breaches, and
      that `applied_failed_open` is deliberately left alone.
External I/O: none.

Operator decision, 2026-09-13 — *"should a run where the veto could not execute
at all stay green under advisory posture? No."*

`proceeded_unvetoed` means **no DeliberationRun exists**: the grace window
expired, buys went to the broker, and nothing reviewed them. The acceptance view
already scored exactly that outcome red when the status read `not_required`
(`buy_veto_missing`), so the board's verdict depended on which status string
described the same fact rather than on the fact.

🪤 **This must not widen to `applied_failed_open`**, where a DeliberationRun
exists and names its own degradation. [DL-125](../../docs/design-log.md) measured
the cost of that: six consecutive nights red for a non-defect, which trains the
operator to ignore the gate. Measured across all **69** `ExecutionRun` rows on
the live spine, 2026-09-13: `advisory` + `proceeded_unvetoed` has occurred **0**
times and `advisory` + `applied_failed_open` **4** times — so the narrow rule
costs no board churn while the wide one would have cost every one of those four.
"""

from __future__ import annotations

import pytest

from orchestration.observatory import breaches
from orchestration.packs.trading_deliberation_view import deliberation
from orchestration.tests.test_trading_deliberation_not_required import (
    _deliberation_graph,
)


def test_unvetoed_advisory_buy_breaches() -> None:
    """🎯 EXEC-OUT-09 / EXEC-OBS-04: an unreviewed buy cannot report green."""
    graph, node = _deliberation_graph("buy", status="proceeded_unvetoed")

    view = deliberation(graph, node)
    found = breaches(view)

    assert view.observed["advisory_attribution"] == "veto_never_ran"
    assert any(breach.key == "advisory_attribution" for breach in found)


def test_unvetoed_advisory_sell_only_run_stays_green() -> None:
    """No buy reached the broker unreviewed, so there is nothing to be red about.

    The gate only produces `proceeded_unvetoed` when the approved set contains a
    buy, so this is a defensive branch rather than a reachable night — but it is
    what keeps the rule about *unreviewed exposure* instead of about a string.
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


@pytest.mark.parametrize("actions", [(), ("buy",), ("buy", "sell")])
def test_failed_open_with_a_reason_is_still_green(actions: tuple[str, ...]) -> None:
    """🪤 DL-125's non-regression: a degraded-but-present veto stays attributed."""
    graph, node = _deliberation_graph(
        *actions,
        status="applied_failed_open",
        failed_open_count=1,
        failed_open_reason="RuntimeError: provider unavailable",
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
