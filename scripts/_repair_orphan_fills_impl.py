"""Append-only orphan Fill repair implementation.

Agent: tooling
Role: adopt broker-known Fill facts without forging ExecutionRun.
External I/O: injected graph and broker order snapshots only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.execution.fill_attempts import fill_attempt_chain
from agents.execution.store import write_fills
from contracts.common import Explanation, Provenance
from contracts.portfolio_manager import OrderIntentSet

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from kernel import GraphStore

_UTC_SUFFIX = "Z"
_ALLOWLIST = {
    "dep-broker-probe-": "dependency probe order; no pipeline Fill expected",
    "probe-s138-": "S138 broker-stop live probe order; no pipeline Fill expected",
}


@dataclass(frozen=True)
class RepairRow:
    """One broker order and the repair verdict for it."""

    client_order_id: str
    ticker: str
    side: str
    quantity: int
    status: str
    verdict: str
    reason: str


@dataclass(frozen=True)
class RepairReport:
    """Aggregate repair result."""

    rows: tuple[RepairRow, ...]
    recorded: int
    would_record: int
    already_recorded: int
    ignored: int


def repair_graph(
    graph: GraphStore,
    broker_fills: tuple[BrokerFill, ...],
    *,
    apply: bool = False,
    since: datetime,
) -> RepairReport:
    """Inspect broker orders and optionally write missing Fill lineage."""
    rows: list[RepairRow] = []
    recorded = would_record = already_recorded = ignored = 0
    for fill in sorted(broker_fills, key=lambda item: item.idempotency_key):
        if not _within_since(fill, since):
            continue
        reason = _allowlist_reason(fill.idempotency_key)
        if reason is not None:
            ignored += 1
            rows.append(_row(fill, "ignored", reason))
            continue
        if fill_attempt_chain(graph, fill.idempotency_key):
            already_recorded += 1
            rows.append(_row(fill, "already_recorded", "Fill chain exists"))
            continue
        if apply:
            write_fills(
                graph,
                run_id=f"repair-orphan-fills:{fill.idempotency_key}",
                fills=(fill,),
                order_set=_order_set_for_fill(graph, fill),
            )
            recorded += 1
            rows.append(_row(fill, "recorded", "wrote through execution.write_fills"))
        else:
            would_record += 1
            rows.append(_row(fill, "would_record", "missing Fill chain"))
    return RepairReport(
        rows=tuple(rows),
        recorded=recorded,
        would_record=would_record,
        already_recorded=already_recorded,
        ignored=ignored,
    )


def parse_time(value: str | None) -> datetime | None:
    """Parse an optional broker timestamp as UTC-aware datetime."""
    if not value:
        return None
    normalized = value.replace(_UTC_SUFFIX, "+00:00")
    return datetime.fromisoformat(normalized).astimezone(UTC)


def _order_set_for_fill(graph: GraphStore, fill: BrokerFill) -> OrderIntentSet | None:
    pm_run_key = _pm_run_key(fill)
    if pm_run_key is None or graph.get_node("PMRun", pm_run_key) is None:
        return None
    return OrderIntentSet(
        run_id=pm_run_key,
        approved=(),
        rejected=(),
        explanation=Explanation(summary="orphan Fill repair lineage"),
        provenance=Provenance(
            run_id=pm_run_key,
            source_agent="portfolio_manager",
            graph_node_id=f"PMRun:{pm_run_key}",
        ),
    )


def _pm_run_key(fill: BrokerFill) -> str | None:
    marker = f":{fill.ticker}:"
    if (
        not fill.idempotency_key.startswith("pm-run-")
        or marker not in fill.idempotency_key
    ):
        return None
    return fill.idempotency_key.split(marker, 1)[0]


def _within_since(fill: BrokerFill, since: datetime) -> bool:
    submitted = parse_time(fill.submitted_at)
    return submitted is None or submitted >= since


def _allowlist_reason(client_order_id: str) -> str | None:
    for prefix, reason in _ALLOWLIST.items():
        if client_order_id.startswith(prefix):
            return reason
    return None


def _row(fill: BrokerFill, verdict: str, reason: str) -> RepairRow:
    return RepairRow(
        client_order_id=fill.idempotency_key,
        ticker=fill.ticker,
        side=fill.side,
        quantity=fill.quantity,
        status=fill.status,
        verdict=verdict,
        reason=reason,
    )
