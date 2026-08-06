"""Execution account snapshot tests.

Agent: execution
Role: prove run-start account facts land on BrokerPositionSnapshot lawfully.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass

from agents.execution.broker import BrokerAccount, BrokerFill, BrokerPosition
from agents.execution.reconciliation import reconcile_run_start
from agents.execution.snapshot_account import account_snapshot_props
from agents.execution.tests.broker_protocol_helpers import NoStopBrokerMixin
from kernel import CollectingFaultSink, InMemoryGraphStore

_DEFAULT_ACCOUNT = BrokerAccount(
    cash_cents=10000000,
    equity_cents=10000000,
    buying_power_cents=10000000,
)


def test_reconcile_run_start_records_account_state_on_snapshot() -> None:
    """EXEC-IDN-03 / EXEC-TRG-07: account facts stay on the
    execution-owned BrokerPositionSnapshot for the run."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    broker = _StaticBroker(
        broker_fills=(),
        broker_positions=(BrokerPosition("AAPL", 2, 10000, 20000),),
        broker_account=BrokerAccount(
            cash_cents=-10496677,
            equity_cents=10404269,
            buying_power_cents=16535900,
        ),
    )

    snapshot = reconcile_run_start(graph, broker, sink, run_id="sched-2026-08-06")

    assert snapshot is not None
    assert snapshot.props["status"] == "fresh"
    assert snapshot.props["account_status"] == "fresh"
    assert snapshot.props["account_cash_cents"] == -10496677
    assert snapshot.props["account_equity_cents"] == 10404269
    assert snapshot.props["account_buying_power_cents"] == 16535900
    assert snapshot.props["run_id"] == "sched-2026-08-06"
    assert sink.faults == []


def test_reconcile_run_start_account_failure_writes_stale_snapshot() -> None:
    """EXEC-OBS-02 / EXEC-TRG-07: account read failure degrades visibly, writes
    a stale snapshot, and raises no exception."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    node = reconcile_run_start(graph, _AccountFailingBroker(), sink, run_id="pm-run")

    assert node is not None
    assert node.props["status"] == "stale"
    assert node.props["account_status"] == "stale"
    assert "broker account read failed" in node.props["account_stale_reason"]
    assert len(sink.faults) == 1


def test_reconcile_run_start_writes_only_execution_owned_snapshot_label() -> None:
    """EXEC-IDN-03: run-start account sync writes no non-execution label."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()

    reconcile_run_start(graph, _StaticBroker((), ()), sink, run_id="owned-label")

    assert _labels_written(graph) == {"BrokerPositionSnapshot"}


def test_account_snapshot_props_without_reason_are_stale_without_detail() -> None:
    """EXEC-OBS-02: stale account props do not invent a missing reason."""
    assert account_snapshot_props(None, None) == {"account_status": "stale"}


@dataclass
class _StaticBroker(NoStopBrokerMixin):
    broker_fills: tuple[BrokerFill, ...]
    broker_positions: tuple[BrokerPosition, ...]
    broker_account: BrokerAccount = _DEFAULT_ACCOUNT

    def submit(self, *_args: object, **_kwargs: object) -> BrokerFill:
        raise AssertionError("reconciliation must not submit")

    def fills(self) -> tuple[BrokerFill, ...]:
        return self.broker_fills

    def positions(self) -> tuple[BrokerPosition, ...]:
        return self.broker_positions

    def account(self) -> BrokerAccount:
        return self.broker_account


class _AccountFailingBroker(NoStopBrokerMixin):
    def submit(self, *_args: object, **_kwargs: object) -> BrokerFill:
        raise AssertionError("reconciliation must not submit")

    def fills(self) -> tuple[BrokerFill, ...]:
        return ()

    def positions(self) -> tuple[BrokerPosition, ...]:
        return ()

    def account(self) -> BrokerAccount:
        raise RuntimeError("offline")


def _labels_written(graph: InMemoryGraphStore) -> set[str]:
    return {label for label, _key in graph._nodes}
