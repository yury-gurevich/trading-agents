"""Dashboard state projections — flags, positions, recovery ladder, bundle.

Agent: surfaces
Role: project supervisor Flags, graph-vs-broker positions, and the DL-36
      escalation/remediation ladder into JSON-ready dicts, run-scoped by the
      run's requested day; assemble the LLM context bundle (DL-47 req. 11).
External I/O: injected GraphStore reads and optional injected AzureReader calls.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from surfaces.dashboard.bundle_azure import bundle_artifacts
from surfaces.dashboard.projections import list_runs, run_request_node, run_stages
from surfaces.queries.flags import flag_ref, resolved_refs

if TYPE_CHECKING:
    from kernel import GraphStore, Node
    from surfaces.dashboard.azure_port import AzureReader
    from surfaces.dashboard.settings import DashboardSettings

_FLAG_FIELDS = ("subject_ref", "severity", "reason", "status", "created_at")
_ESCALATION_FIELDS = (
    "agent_type",
    "failed_credentials",
    "mode",
    "auto_attempts",
    "status",
    "created_at",
)
_PLAN_FIELDS = (
    "escalation_key",
    "remediation",
    "rationale",
    "auto_eligible",
    "status",
    "created_at",
)


def _run_day(graph: GraphStore, run_id: str) -> str:
    """The run's requested day (ISO date) — the scoping window for state nodes."""
    node = run_request_node(graph, run_id)
    return str(node.props.get("requested_at", "")) if node else ""


def _row(node: Node, fields: tuple[str, ...]) -> dict[str, object]:
    row: dict[str, object] = {"key": node.key}
    row.update({name: node.props.get(name) for name in fields})
    return row


def _in_scope(node: Node, day: str) -> bool:
    """Run-scoped = created on the run's day; anything still pending/open rides too."""
    created = str(node.props.get("created_at", ""))
    status = str(node.props.get("status", ""))
    return (bool(day) and created.startswith(day)) or status in ("pending", "open")


def run_flags(graph: GraphStore, run_id: str) -> list[dict[str, object]]:
    """Supervisor-path Flags scoped to the run day, plus everything pending.

    Flag props are append-only, so resolution truth is the matching
    FlagResolution record: a resolved flag stays visible on its own run day
    (with status "resolved") but no longer rides into every other run.
    """
    day = _run_day(graph, run_id)
    resolved = resolved_refs(graph)
    rows = []
    for node in graph.list_nodes("Flag"):
        done = flag_ref(node) in resolved
        created = str(node.props.get("created_at", ""))
        same_day = bool(day) and created.startswith(day)
        if not same_day and (done or not _in_scope(node, day)):
            continue
        row = _row(node, _FLAG_FIELDS)
        if done:
            row["status"] = "resolved"
        rows.append(row)
    rows.sort(key=lambda r: str(r.get("created_at", "")), reverse=True)
    return rows


def run_positions(graph: GraphStore, run_id: str) -> dict[str, object]:
    """Open graph Positions joined against the latest broker snapshot per ticker."""
    del run_id  # positions are current state; the run selects context, not history
    graph_qty: dict[str, int] = {}
    for node in graph.list_nodes("Position"):
        props = node.props
        if str(props.get("status", "open")) != "open":
            continue
        if props.get("broker_absent") or props.get("broker_superseded_by"):
            continue
        ticker = str(props["ticker"])
        graph_qty[ticker] = graph_qty.get(ticker, 0) + int(str(props["quantity"]))
    snapshot = _latest_snapshot(graph)
    broker_qty: dict[str, int] = {}
    holdings = snapshot.props.get("holdings", ()) if snapshot else ()
    for holding in holdings if isinstance(holdings, (list, tuple)) else ():
        broker_qty[str(holding["ticker"])] = int(str(holding["quantity"]))
    rows = [
        {
            "ticker": ticker,
            "graph_qty": graph_qty.get(ticker),
            "broker_qty": broker_qty.get(ticker),
            "match": graph_qty.get(ticker) == broker_qty.get(ticker),
        }
        for ticker in sorted(set(graph_qty) | set(broker_qty))
    ]
    return {
        "snapshot_key": snapshot.key if snapshot else None,
        "snapshot_at": (
            str(snapshot.props.get("created_at", "")) if snapshot else None
        ),
        "rows": rows,
    }


def run_recovery(graph: GraphStore, run_id: str) -> dict[str, object]:
    """The DL-36 ladder: escalations + remediation plans in the run's scope."""
    day = _run_day(graph, run_id)
    escalations = [
        _row(node, _ESCALATION_FIELDS)
        for node in graph.list_nodes("Escalation")
        if _in_scope(node, day)
    ]
    plans = [
        _row(node, _PLAN_FIELDS)
        for node in graph.list_nodes("RemediationPlan")
        if _in_scope(node, day)
    ]
    return {"escalations": escalations, "remediation_plans": plans}


def run_bundle(
    graph: GraphStore,
    run_id: str,
    azure: AzureReader | None = None,
    settings: DashboardSettings | None = None,
) -> dict[str, object]:
    """The LLM context bundle with bounded per-container logs and fleet images."""
    from surfaces.dashboard.projections_verdict import verdict_projection
    from surfaces.dashboard.settings import DashboardSettings

    config = settings or DashboardSettings()
    node = run_request_node(graph, run_id)
    tickers = node.props.get("tickers", ()) if node else ()
    logs: dict[str, object] = {
        "available": False,
        "message": "Log Analytics data unavailable",
        "containers": {},
    }
    images: dict[str, object] = {
        "available": False,
        "message": "Azure image data unavailable",
        "containers": {},
    }
    if settings is not None:
        logs, images = bundle_artifacts(azure, settings, _run_day(graph, run_id))
    return {
        "run_id": run_id,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "meta": {
            "requested_at": _run_day(graph, run_id),
            "ticker_count": (len(tickers) if isinstance(tickers, (list, tuple)) else 0),
            "known_runs": [str(r["run_id"]) for r in list_runs(graph)],
        },
        "verdict": verdict_projection(graph, run_id, azure, config),
        "stages": run_stages(graph, run_id),
        "flags": run_flags(graph, run_id),
        "positions": run_positions(graph, run_id),
        "recovery": run_recovery(graph, run_id),
        "logs": logs,
        "images": images,
    }


def _latest_snapshot(graph: GraphStore) -> Node | None:
    nodes = graph.list_nodes("BrokerPositionSnapshot")
    if not nodes:
        return None
    return max(nodes, key=lambda n: str(n.props.get("created_at", "")))
