"""Read-only S237 fidelity export from the graph store.

Agent: tooling
Role: project each scheduled live run into one JSON of what its stages read and decided.
External I/O: writes JSON files outside the repository worktree.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.fidelity_export_book import book_for
from scripts.fidelity_export_helpers import (
    child,
    deploy_for,
    is_linked,
    node_block,
    node_props,
    nodes_to_props,
    parse_dt,
    regime_for,
    resolved,
)
from scripts.fidelity_export_outcomes import (
    benchmark_gap,
    deliberation_block,
    execution_block,
    fills_for,
)

if TYPE_CHECKING:
    from kernel.graph import GraphStore, Node

_ROOT = Path(__file__).resolve().parents[1]
_SCHED = re.compile(r"^sched-\d{4}-\d{2}-\d{2}$")


def refuse_worktree_out(out: Path) -> Path:
    """Return a resolved output dir, rejecting paths inside this worktree."""
    resolved_out = out.resolve()
    try:
        resolved_out.relative_to(_ROOT.resolve())
    except ValueError:
        return resolved_out
    raise ValueError(f"fidelity export path is inside the worktree: {out}")


def export_sessions(
    graph: GraphStore, *, start: date, end: date, out: Path
) -> tuple[Path, ...]:
    """Write one JSON file per scheduled run in the inclusive date range."""
    target = refuse_worktree_out(out)
    payloads = [_session_payload(graph, node) for node in _scheduled(graph, start, end)]
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for payload in payloads:
        path = target / f"{payload['run_id']}.json"
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        written.append(path)
    return tuple(written)


def _scheduled(graph: GraphStore, start: date, end: date) -> tuple[Node, ...]:
    """`sched-YYYY-MM-DD` RunRequests only: no manual, resume or link keys."""
    rows = [
        node
        for node in graph.list_nodes("RunRequest")
        if _SCHED.fullmatch(str(node.props.get("run_id", "")))
        and start <= date.fromisoformat(str(node.props["run_id"])[6:]) <= end
    ]
    return tuple(sorted(rows, key=lambda node: str(node.props["run_id"])))


def _chain_root(graph: GraphStore, request: Node) -> Node:
    """The run the fleet finished the session in: its latest resume, else itself."""
    resumes = [
        node
        for node in graph.ancestors(request, max_depth=1, edge_types={"RESUMES"})
        if node.label == "RunRequest"
    ]
    if not resumes:
        return request
    return max(
        resumes, key=lambda node: (str(node.props.get("resumed_at", "")), node.key)
    )


def _session_payload(graph: GraphStore, request: Node) -> dict[str, object]:
    run_id = str(request.props["run_id"])
    root = _chain_root(graph, request)
    market = child(graph, root, "INGESTED_BY", "MarketData")
    scan_raw = child(graph, market, "SCANNED_BY", "ScanRun")
    analyst_raw = child(graph, scan_raw, "ANALYZED_BY", "AnalystRun")
    pm_raw = child(graph, analyst_raw, "EVALUATED_BY", "PMRun")
    scan, analyst, pm = (
        resolved(graph, node) for node in (scan_raw, analyst_raw, pm_raw)
    )
    read_by = (
        parse_dt((pm or analyst).props.get("created_at")) if pm or analyst else None
    )
    read_run_id = str(market.props.get("run_id", run_id)) if market else run_id
    book = book_for(graph, read_run_id, read_by)
    scanner = node_block(scan, "candidate_set", "filter_trace", "created_at")
    analyst_block = node_block(analyst, "recommendation_set", "created_at")
    market_block = node_block(market, "snapshot", "tickers", "window_end", "run_id")
    gaps = set(book.gaps)
    if benchmark_gap(market_block.get("snapshot"), scanner, analyst_block):
        gaps.add("benchmark")
    stages = (market, scan_raw, analyst_raw, pm_raw)
    return {
        "run_id": run_id,
        "session": run_id.removeprefix("sched-"),
        "resumed": root is not request or any(is_linked(node) for node in stages),
        "deploy": deploy_for(graph, scan),
        "market": market_block,
        "regime": regime_for(graph, market),
        "book": {"key": book.snapshot.key, "props": node_props(book.snapshot)}
        if book.snapshot is not None
        else {},
        "positions": list(book.positions),
        "scanner": scanner,
        "analyst": analyst_block,
        "pm": _pm_block(graph, pm),
        "deliberation": deliberation_block(
            resolved(graph, child(graph, pm_raw, "DELIBERATED_BY", "DeliberationRun"))
        ),
        "execution": execution_block(
            resolved(graph, child(graph, pm_raw, "EXECUTED_BY", "ExecutionRun"))
        ),
        "fills": fills_for(graph, (pm_raw.key if pm_raw else "", pm.key if pm else "")),
        "not_persisted": sorted(gaps),
    }


def _pm_block(graph: GraphStore, pm: Node | None) -> dict[str, object]:
    if pm is None:
        return {}
    return {
        **node_block(pm, "created_at"),
        "order_intents": nodes_to_props(
            graph.ancestors(pm, max_depth=1, edge_types={"EMITTED_BY"})
        ),
        "rejections": nodes_to_props(
            graph.ancestors(pm, max_depth=1, edge_types={"REJECTED_IN"})
        ),
    }
