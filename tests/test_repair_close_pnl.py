"""Repair script tests for decision-time close PnL invalidation.

Agent: tooling
Role: verify append-only repair behavior for CloseDecision.pnl_cents defects.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime

from scripts.repair_close_pnl import REASON, _print_report, repair_graph

from kernel import InMemoryGraphStore

_NOW = datetime(2026, 7, 23, 0, 0, tzinfo=UTC)


def test_dry_run_writes_nothing() -> None:
    graph = InMemoryGraphStore()
    _close(graph, "amd", ticker="AMD", pnl_cents=-153065)

    report = repair_graph(graph, now=_NOW)

    node = graph.get_node("CloseDecision", "close:amd")
    assert node is not None
    assert "pnl_invalidated_at" not in node.props
    assert report.invalidated == 1
    assert report.rows[0].verdict == "would_invalidate"


def test_apply_stamps_unfilled_decision_and_second_run_skips() -> None:
    graph = InMemoryGraphStore()
    _close(graph, "csco", ticker="CSCO", pnl_cents=-3540)

    first = repair_graph(graph, apply=True, now=_NOW)
    second = repair_graph(graph, apply=True, now=_NOW)

    node = graph.get_node("CloseDecision", "close:csco")
    assert node is not None
    assert node.props["pnl_cents"] == -3540
    assert node.props["pnl_invalidated_at"] == "2026-07-23T00:00:00+00:00"
    assert node.props["pnl_invalidated_reason"] == REASON
    assert first.invalidated == 1
    assert second.invalidated == 0
    assert second.skipped_invalidated == 1
    assert second.rows == ()


def test_filled_sell_is_left_for_manual_review() -> None:
    graph = InMemoryGraphStore()
    position = _close(graph, "hpe", ticker="HPE", pnl_cents=106027)
    graph.merge_node(
        "Fill",
        "monitor-run:HPE:sell:pm:hpe",
        {
            "ticker": "HPE",
            "side": "sell",
            "status": "filled",
            "broker_status": "filled",
        },
    )

    report = repair_graph(graph, apply=True, now=_NOW)

    node = graph.get_node("CloseDecision", "close:hpe")
    assert position.key == "pm:hpe"
    assert node is not None
    assert "pnl_invalidated_at" not in node.props
    assert report.manual_review == 1
    assert report.rows[0].verdict == "manual_review_filled_sell"


def test_print_report_includes_table_and_totals(capsys) -> None:
    graph = InMemoryGraphStore()
    _close(graph, "mrvl", ticker="MRVL", pnl_cents=-66880)
    report = repair_graph(graph, now=_NOW)

    _print_report(report, apply=False)

    out = capsys.readouterr().out
    assert "mode=dry-run" in out
    assert "ticker\ttrigger\tpnl_cents\tverdict" in out
    assert "MRVL\tstop\t-66880\twould_invalidate" in out
    assert "totals candidates=1 invalidated=1 manual_review=0" in out


def _close(graph: InMemoryGraphStore, key: str, *, ticker: str, pnl_cents: int):
    position = graph.merge_node(
        "Position",
        f"pm:{key}",
        {"ticker": ticker, "status": "open"},
    )
    close = graph.merge_node(
        "CloseDecision",
        f"close:{key}",
        {
            "ticker": ticker,
            "position_id": position.key,
            "trigger": "stop",
            "pnl_cents": pnl_cents,
        },
    )
    graph.add_edge(close, position, "CLOSES")
    return position
