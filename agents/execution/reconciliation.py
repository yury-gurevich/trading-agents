"""Run-start broker reconciliation for execution graph-pull work.

Agent: execution
Role: refresh pending fills, snapshot broker holdings, and flag graph divergence.
External I/O: injected Broker and GraphStore backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from agents.execution.reconciliation_store import (
    position_divergences,
    refresh_pending_fills,
    write_divergence_flag,
    write_snapshot,
)
from kernel import fault_boundary

if TYPE_CHECKING:
    from agents.execution.broker import (
        Broker,
        BrokerAccount,
        BrokerFill,
        BrokerPosition,
    )
    from kernel import FaultSink, GraphStore, Node


class _AccountReadableBroker(Protocol):
    """Narrow account-read surface used only by run-start reconciliation."""

    def account(self) -> BrokerAccount:
        """Return read-only broker account state."""
        ...  # pragma: no cover - protocol declaration only.


def reconcile_run_start(
    graph: GraphStore, broker: Broker, sink: FaultSink, *, run_id: str
) -> Node | None:
    """Run fail-open broker reconciliation before execution submits new intents."""
    broker_fills = _read_fills(broker, sink)
    if broker_fills is not None:
        refresh_pending_fills(graph, broker_fills, sink)
    positions, stale_reason = _read_positions(broker, sink)
    if positions is None:
        return write_snapshot(
            graph,
            run_id=run_id,
            holdings=(),
            account=None,
            status="stale",
            stale_reason=stale_reason,
        )
    account, account_stale_reason = _read_account(broker, sink)
    if account is None:
        return write_snapshot(
            graph,
            run_id=run_id,
            holdings=positions,
            account=None,
            status="stale",
            stale_reason=account_stale_reason,
        )
    snapshot = write_snapshot(
        graph,
        run_id=run_id,
        holdings=positions,
        account=account,
        status="fresh",
        stale_reason=None,
    )
    divergences = position_divergences(graph, positions)
    if divergences:
        write_divergence_flag(graph, snapshot=snapshot, divergences=divergences)
    return snapshot


def _read_fills(broker: Broker, sink: FaultSink) -> tuple[BrokerFill, ...] | None:
    try:
        return broker.fills()
    except Exception as exc:
        _record_fault(sink, f"broker fills read failed: {type(exc).__name__}")
        return None


def _read_positions(
    broker: Broker, sink: FaultSink
) -> tuple[tuple[BrokerPosition, ...] | None, str | None]:
    try:
        return (broker.positions(), None)
    except Exception as exc:
        reason = f"broker positions read failed: {type(exc).__name__}"
        _record_fault(sink, reason)
        return (None, reason)


def _read_account(
    broker: Broker, sink: FaultSink
) -> tuple[BrokerAccount | None, str | None]:
    try:
        return (cast("_AccountReadableBroker", broker).account(), None)
    except Exception as exc:
        reason = f"broker account read failed: {type(exc).__name__}"
        _record_fault(sink, reason)
        return (None, reason)


def _record_fault(sink: FaultSink, message: str) -> None:
    with fault_boundary(
        sink,
        agent="execution",
        module="agents.execution.reconciliation",
        capability="reconcile_run_start",
        reraise=False,
    ):
        raise RuntimeError(message)
