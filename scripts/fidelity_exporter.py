"""Read-only S237 fidelity export from the graph store.

Agent: tooling
Role: project scheduled live runs into JSON fixtures for replay fidelity.
External I/O: writes JSON files outside the repository worktree.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.fidelity_export_helpers import (
    fills_for_pm,
    held_stop_inputs,
    node_payload,
    node_props,
    nodes_to_props,
    not_persisted_fields,
    parse_dt,
)

if TYPE_CHECKING:
    from kernel.graph import GraphStore, Node

_ROOT = Path(__file__).resolve().parents[1]
_SCHED = re.compile(r"^sched-\d{4}-\d{2}-\d{2}$")


def refuse_worktree_out(out: Path) -> Path:
    """Return a resolved output dir, rejecting paths inside this worktree."""
    resolved = out.resolve()
    try:
        resolved.relative_to(_ROOT.resolve())
    except ValueError:
        return resolved
    raise ValueError(f"fidelity export path is inside the worktree: {out}")


def export_sessions(
    graph: GraphStore, *, start: date, end: date, out: Path
) -> tuple[Path, ...]:
    """Write one JSON file per scheduled run in the inclusive date range."""
    target = refuse_worktree_out(out)
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for request in _scheduled_requests(graph, start, end):
        payload = _session_payload(graph, request)
        path = target / f"{payload['run_id']}.json"
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        written.append(path)
    return tuple(written)


def _scheduled_requests(graph: GraphStore, start: date, end: date) -> tuple[Node, ...]:
    rows: list[Node] = []
    for node in graph.list_nodes("RunRequest"):
        run_id = str(node.props.get("run_id", node.key.removeprefix("request:")))
        if not _SCHED.fullmatch(run_id):
            continue
        session = date.fromisoformat(run_id.removeprefix("sched-"))
        if start <= session <= end:
            rows.append(node)
    return tuple(sorted(rows, key=lambda item: str(item.props.get("run_id", item.key))))


def _session_payload(graph: GraphStore, request: Node) -> dict[str, object]:
    run_id = str(request.props.get("run_id", request.key.removeprefix("request:")))
    market = _linked(graph, request, "INGESTED_BY", "MarketData")
    scan_raw = _linked(graph, market, "SCANNED_BY", "ScanRun")
    scan = _resolved(graph, scan_raw)
    analyst_raw = _linked(graph, scan_raw or scan, "ANALYZED_BY", "AnalystRun")
    analyst = _resolved(graph, analyst_raw)
    pm_raw = _linked(graph, analyst_raw or analyst, "EVALUATED_BY", "PMRun")
    pm = _resolved(graph, pm_raw)
    delib_raw = _linked(graph, pm_raw or pm, "DELIBERATED_BY", "DeliberationRun")
    delib = _resolved(graph, delib_raw)
    execution_raw = _linked(graph, pm_raw or pm, "EXECUTED_BY", "ExecutionRun")
    execution = _resolved(graph, execution_raw)
    book = _linked(graph, request, "REFRESHES", "BrokerPositionSnapshot")
    not_persisted = not_persisted_fields(market, book)
    resumed = any(
        node is not None and "linked_from_key" in node.props
        for node in (scan_raw, analyst_raw, pm_raw, delib_raw, execution_raw)
    )
    return {
        "run_id": run_id,
        "session": run_id.removeprefix("sched-"),
        "resumed": resumed,
        "deploy": _deploy_for(graph, scan_raw or scan),
        "market": node_payload("MarketData", market, "snapshot"),
        "regime": _regime(graph, market),
        "book": node_props(book),
        "held_stop_inputs": held_stop_inputs(graph, book),
        "scanner": node_payload("ScanRun", scan, "candidate_set"),
        "analyst": node_payload("AnalystRun", analyst, "recommendation_set"),
        "pm": {
            **node_payload("PMRun", pm, "order_intent_set"),
            "order_intents": nodes_to_props(
                graph.ancestors(pm, max_depth=1, edge_types={"EMITTED_BY"})
                if pm
                else ()
            ),
            "rejections": nodes_to_props(
                graph.ancestors(pm, max_depth=1, edge_types={"REJECTED_IN"})
                if pm
                else ()
            ),
        },
        "deliberation": node_props(delib),
        "execution": node_props(execution),
        "fills": fills_for_pm(graph, pm),
        "not_persisted": sorted(not_persisted),
    }


def _linked(graph: GraphStore, node: Node | None, edge: str, label: str) -> Node | None:
    if node is None:
        return None
    return next(
        (
            item
            for item in graph.descendants(node, max_depth=1, edge_types={edge})
            if item.label == label
        ),
        None,
    )


def _resolved(graph: GraphStore, node: Node | None) -> Node | None:
    if node is None:
        return None
    linked = node.props.get("linked_from_key")
    if linked:
        return graph.get_node(node.label, str(linked)) or node
    return node


def _regime(graph: GraphStore, market: Node | None) -> dict[str, object]:
    if market is None:
        return {}
    run_id = str(market.props.get("run_id", ""))
    node = graph.get_node("RegimeContext", f"regime-context:{run_id}")
    snapshot = node_props(node).get("snapshot", {}) if node else {}
    return snapshot if isinstance(snapshot, dict) else {}


def _deploy_for(graph: GraphStore, scan: Node | None) -> dict[str, object]:
    scan_at = parse_dt(scan.props.get("created_at")) if scan else None
    candidates = []
    for node in graph.list_nodes("DeployRecord"):
        deployed_at = parse_dt(node.props.get("deployed_at"))
        if scan_at is None or deployed_at is None or deployed_at <= scan_at:
            floor = datetime.min.replace(tzinfo=UTC)
            candidates.append((deployed_at or floor, node))
    if not candidates:
        return {}
    return node_props(max(candidates, key=lambda item: item[0])[1])
