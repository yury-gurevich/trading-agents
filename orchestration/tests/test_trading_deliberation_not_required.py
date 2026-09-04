"""Trading deliberation not-required acceptance tests for S191.

Agent: orchestration
Role: prove advisory not_required verdicts depend on approved buys, not race order.
External I/O: none.
"""

from __future__ import annotations

import pytest

from kernel import InMemoryGraphStore, Node
from orchestration.observatory import breaches
from orchestration.packs.trading_deliberation_view import deliberation


def _order_intent_set(*actions: str) -> dict[str, object]:
    tickers = ("AAPL", "MSFT", "GOOG")
    return {
        "run_id": "pm-run",
        "approved": tuple(
            {
                "ticker": ticker,
                "action": action,
                "quantity": 1,
                "est_price": {"amount": "100.00", "currency": "USD"},
                "rationale": {"summary": f"{action} {ticker}", "evidence_refs": ()},
            }
            for ticker, action in zip(tickers, actions, strict=False)
        ),
        "rejected": (),
        "explanation": {"summary": "PM decision", "evidence_refs": ()},
        "provenance": {"run_id": "pm-run", "source_agent": "portfolio_manager"},
    }


def _deliberation_graph(
    *actions: str,
    posture: str = "advisory",
    status: str = "not_required",
    failed_open_count: int = 0,
    failed_open_reason: str = "",
    order_payload: object | None = None,
    reviewed: bool = False,
) -> tuple[InMemoryGraphStore, Node]:
    graph = InMemoryGraphStore()
    pm_run = graph.merge_node(
        "PMRun",
        "pm-run",
        {"order_intent_set": order_payload or _order_intent_set(*actions)},
    )
    verdicts = {"AAPL": "uphold"} if reviewed else {}
    debates = {"AAPL": {"verdict": "uphold", "turns": []}} if reviewed else {}
    delib = graph.merge_node(
        "DeliberationRun",
        "delib-run",
        {
            "verdicts": verdicts,
            "vetoed_tickers": (),
            "debates": debates,
            "real_debate_count": 0,
            "failed_open_count": failed_open_count,
            "failed_open_reason": failed_open_reason,
        },
    )
    execution = graph.merge_node(
        "ExecutionRun",
        "exec-run",
        {
            "deliberation_posture": posture,
            "deliberation_status": status,
            "submitted": len(actions),
        },
    )
    graph.add_edge(pm_run, delib, "DELIBERATED_BY")
    graph.add_edge(pm_run, execution, "EXECUTED_BY")
    return graph, delib


def test_not_required_advisory_with_no_approved_buy_is_attributed() -> None:
    """EXEC-OUT-09 / EXEC-OBS-04: quiet advisory not_required has a cause."""
    graph, node = _deliberation_graph()

    view = deliberation(graph, node)

    assert view.observed["advisory_attribution"] == "ok"
    assert breaches(view) == ()


def test_not_required_advisory_sell_only_run_is_attributed() -> None:
    """EXEC-OUT-09 / EXEC-OBS-04: sell-only not_required needs no veto."""
    graph, node = _deliberation_graph("sell")

    view = deliberation(graph, node)

    assert view.observed["advisory_attribution"] == "ok"
    assert breaches(view) == ()


def test_not_required_advisory_with_approved_buy_still_breaches() -> None:
    """EXEC-OUT-09 / EXEC-OBS-04: not_required cannot hide a skipped buy veto."""
    graph, node = _deliberation_graph("buy")

    view = deliberation(graph, node)
    found = breaches(view)

    assert view.observed["advisory_attribution"] == "buy_veto_missing"
    assert any(breach.key == "advisory_attribution" for breach in found)


def test_not_required_advisory_with_unreadable_pm_payload_still_breaches() -> None:
    """EXEC-OUT-09 / EXEC-OBS-04: unreadable PM approved set is not no-buy."""
    graph, node = _deliberation_graph(order_payload={"approved": "not-contract"})

    view = deliberation(graph, node)
    found = breaches(view)

    assert view.observed["advisory_attribution"] == "missing"
    assert any(breach.key == "advisory_attribution" for breach in found)


@pytest.mark.parametrize("status", ["not_required", "applied"])
def test_quiet_advisory_ordering_statuses_share_verdict(status: str) -> None:
    """EXEC-OUT-09 / EXEC-OBS-04: quiet ordering race no longer changes verdict."""
    graph, node = _deliberation_graph(status=status)

    assert breaches(deliberation(graph, node)) == ()


def test_binding_branch_still_uses_coverage_and_fail_open_checks() -> None:
    """EXEC-OUT-09 / EXEC-OBS-04: binding still checks coverage and fail-open count."""
    graph, node = _deliberation_graph(
        "buy",
        posture="binding",
        status="applied_failed_open",
        failed_open_count=1,
        failed_open_reason="RuntimeError: provider unavailable",
        reviewed=True,
    )

    found = breaches(deliberation(graph, node))
    keys = {breach.key for breach in found}

    assert "debate_coverage" in keys
    assert "failed_open_count" in keys
    assert "advisory_attribution" not in keys


@pytest.mark.parametrize(
    ("status", "failed_open_count", "failed_open_reason"),
    [
        ("applied", 0, ""),
        ("applied_failed_open", 1, "RuntimeError: provider unavailable"),
        ("proceeded_unvetoed", 0, ""),
    ],
)
def test_existing_advisory_statuses_stay_attributed(
    status: str, failed_open_count: int, failed_open_reason: str
) -> None:
    """EXEC-OUT-09 / EXEC-OBS-04: existing advisory status handling is unchanged."""
    graph, node = _deliberation_graph(
        status=status,
        failed_open_count=failed_open_count,
        failed_open_reason=failed_open_reason,
    )

    assert breaches(deliberation(graph, node)) == ()
