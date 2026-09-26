"""Probe orders need no pipeline Fill, in the audit and in the orphan repair alike.

Agent: tooling
Role: prove one probe allowlist serves both broker/graph scripts.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from scripts._broker_probe_orders import probe_order_reason
from scripts.audit_broker_graph import audit_graph
from scripts.repair_orphan_fills import repair_graph

from agents.execution.broker import BrokerFill
from contracts.common import Money
from kernel import InMemoryGraphStore

# The four probe orders the live audit failed on 2026-09-26 (planner probes on F and T).
_MEASURED_PROBES = (
    "replace-probe-2026-09-25",
    "s230-livecheck-4e22c579-a",
    "s230-livecheck-4e22c579-b",
    "stop:probe-s164:T#1",
)


@pytest.mark.parametrize("key", _MEASURED_PROBES)
def test_a_planner_probe_order_is_skipped_by_the_audit(key: str) -> None:
    """EXEC-OBS-01 / EXEC-OBS-02: a probe order is named, not failed, by A3."""
    report = audit_graph(InMemoryGraphStore(), (), (_order(key),))

    [row] = [row for row in report.rows if row.check == "A3"]
    assert (row.verdict, row.subject) == ("SKIP", key)
    assert report.failures == 0


def test_a_pipeline_order_without_a_fill_still_fails() -> None:
    """EXEC-OBS-01: the allowlist names probes; it does not excuse pipeline orders."""
    report = audit_graph(InMemoryGraphStore(), (), (_order("pm-run-x:AAPL:buy"),))

    assert [row.verdict for row in report.rows if row.check == "A3"] == ["FAIL"]
    assert probe_order_reason("stop:0aa58b5c2f2ff8b9:CSCO#1") is None


def test_the_repair_never_writes_a_fill_for_a_probe() -> None:
    """EXEC-OBS-01 / EXEC-OBS-02: `--apply` skips exactly what the audit skips."""
    graph = InMemoryGraphStore()
    orders = tuple(_order(key) for key in _MEASURED_PROBES)
    report = repair_graph(
        graph, orders, apply=True, since=datetime(2026, 9, 1, tzinfo=UTC)
    )

    assert {row.verdict for row in report.rows} == {"ignored"}
    assert graph.list_nodes("Fill") == ()


def _order(key: str) -> BrokerFill:
    return BrokerFill(
        idempotency_key=key,
        ticker="F",
        side="buy",
        quantity=1,
        price=Money(amount=Decimal("50.00")),
        broker_order_id=f"broker:{key}",
        status="rejected",
        submitted_at="2026-09-25T08:03:00Z",
    )
