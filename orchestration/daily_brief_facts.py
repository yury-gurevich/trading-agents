"""Select one run's brief facts from the graph: every figure as its owner stored it.

Agent: orchestration
Role: gather the verdict, money, scoreboard, orders, fills and needs-you for one run.
External I/O: reads the injected GraphStore.

Nothing here decides or recomputes. The verdict is `accept_run`'s, needs-you is
`compute_health`'s, and the equity and the vs-SPY clause are the reporter's Snapshot
as stored (DL-231, `DSP-OUT-06`).
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from agents.supervisor.domain.health import compute_health
from contracts.run_posture import RUN_POSTURE_DEGRADED, run_posture
from orchestration.batch_chain import CHAIN, POSITION_SYNC_KEY
from orchestration.daily_brief_fills import fills_between, parse_instant, run_orders
from orchestration.daily_brief_text import (
    NOT_FINISHED,
    BriefDataError,
    BriefFacts,
    local_stamp,
)
from orchestration.packs.trading_acceptance import accept_run
from orchestration.packs.trading_observatory_views import SPEC

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore, Node

_SCHEDULED = "sched-"
# The reporter's own clause, the tail of `headline_summary` (snapshot_result.py).
_CLAUSE = re.compile(r"(?:vs \S+|Performance): .+")
_CHAIN_EDGES = {edge for edge, _ in CHAIN}
_STAGE_NAMES = {label: name for name, label, _, _ in SPEC}
_FINISH_ORDER = (POSITION_SYNC_KEY, *(label for _, label in CHAIN))


@dataclass(frozen=True)
class _Reference:
    run_id: str
    created: datetime
    equity_cents: int | None


def brief_facts(
    graph: GraphStore,
    run_id: str,
    nodes: Mapping[str, Node],
    *,
    now: datetime,
    timezone: str,
) -> BriefFacts:
    """Return what the brief says about ``run_id``; no Snapshot means the RED brief."""
    health = compute_health(graph, None)
    fills = graph.list_nodes("Fill")
    pm_run = nodes.get("PMRun")
    facts = BriefFacts(
        verdict=NOT_FINISHED,
        run_id=run_id,
        stamp=local_stamp(now, timezone),
        degraded=run_posture(nodes["RunRequest"].props) == RUN_POSTURE_DEGRADED,
        orders=run_orders(fills, _source_key(pm_run)) if pm_run is not None else (),
        open_incidents=health["open_incidents"],
        critical_flags=health["pending_human_flags"],
        last_stage=_last_stage(nodes),
    )
    snapshot = nodes.get("Snapshot")
    if snapshot is None or pm_run is None:
        return facts
    created = parse_instant(pm_run.props.get("created_at"))
    if created is None:
        raise BriefDataError("PMRun.created_at")
    reference = _previous_run(graph, run_id, created)
    return replace(
        facts,
        verdict=accept_run(graph, run_id).verdict,
        equity_cents=_equity(snapshot),
        previous_run=reference.run_id if reference else None,
        previous_cents=reference.equity_cents if reference else None,
        scoreboard=_clause(snapshot),
        fills=fills_between(fills, reference.created if reference else None, created),
        last_stage=None,
    )


def _source_key(pm_run: Node) -> str:
    """A resumed run's PMRun links to the decision its Fills name (resume.py)."""
    return str(pm_run.props.get("linked_from_key") or pm_run.key)


def _last_stage(nodes: Mapping[str, Node]) -> str | None:
    finished = [label for label in _FINISH_ORDER if label in nodes]
    return _STAGE_NAMES.get(finished[-1]) if finished else None


def _previous_run(
    graph: GraphStore, run_id: str, created: datetime
) -> _Reference | None:
    """The latest earlier scheduled run with a Snapshot, by PMRun time (DL-225)."""
    pm_times = {
        node.key: parse_instant(node.props.get("created_at"))
        for node in graph.list_nodes("PMRun")
    }
    earlier: list[tuple[datetime, str, Node]] = []
    for snapshot in graph.list_nodes("Snapshot"):
        when = pm_times.get(str(snapshot.props.get("run_id", "")))
        if when is not None and when < created:
            earlier.append((when, snapshot.key, snapshot))
    for when, _, snapshot in sorted(earlier, key=lambda item: item[:2], reverse=True):
        name = _run_name(graph, snapshot)
        if name.startswith(_SCHEDULED) and name != run_id:
            return _Reference(name, when, _earlier_equity(snapshot))
    return None


def _run_name(graph: GraphStore, snapshot: Node) -> str:
    upstream = graph.ancestors(snapshot, max_depth=len(CHAIN), edge_types=_CHAIN_EDGES)
    request = next((node for node in upstream if node.label == "RunRequest"), None)
    return str(request.props.get("run_id", "")) if request is not None else ""


def _earlier_equity(snapshot: Node) -> int | None:
    # Another run's malformed Snapshot is its own defect, not a reason to stay silent.
    try:
        return _equity(snapshot)
    except BriefDataError:
        return None


def _equity(snapshot: Node) -> int | None:
    """The stored equity in integer cents, or None when the report has no figure."""
    metrics = snapshot.props.get("metrics")
    if not isinstance(metrics, Mapping):
        raise BriefDataError("Snapshot.metrics")
    group = metrics.get("performance")
    if group is None:  # reported before the scoreboard existed, or degraded
        return None
    if not isinstance(group, Mapping):
        raise BriefDataError("Snapshot.metrics.performance")
    sessions = _number(group, "performance_sessions")
    equity = _number(group, "equity_cents")
    # Zero sessions is the reporter's contained failure: its 0.0 is not a figure.
    return round(equity) if sessions > 0 else None


def _number(group: Mapping[str, object], name: str) -> float:
    value = group.get(name)
    if isinstance(value, bool) or not isinstance(value, int | float):
        value = math.nan  # malformed reads as not a number, and fails below
    if not math.isfinite(value):
        raise BriefDataError(f"Snapshot.metrics.performance.{name}")
    return float(value)


def _clause(snapshot: Node) -> str | None:
    headline = snapshot.props.get("headline_summary")
    match = _CLAUSE.search(headline) if isinstance(headline, str) else None
    return match.group(0) if match else None
