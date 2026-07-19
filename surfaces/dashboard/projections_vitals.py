"""Dashboard status-line vitals projection.

Agent: surfaces
Role: summarize flags, sync, feed degradation, reachability, images, cost, and fire.
External I/O: injected GraphStore reads and AzureReader calls only.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

from contracts.feed_notes import degraded_feed_name
from orchestration.batch_trace import walk_chain
from surfaces.dashboard.projections import list_runs
from surfaces.dashboard.projections_infra import infra_projection
from surfaces.dashboard.projections_state import run_positions
from surfaces.queries.flags import pending_flags

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore
    from surfaces.dashboard.azure_port import AzureReader
    from surfaces.dashboard.github_builds import GitHubReader
    from surfaces.dashboard.settings import DashboardSettings


def vitals_projection(
    graph: GraphStore,
    azure: AzureReader | None,
    settings: DashboardSettings,
    run_id: str | None,
    *,
    now: datetime | None = None,
    github: GitHubReader | None = None,
) -> dict[str, object]:
    """Project every DL-47 status-line vital from current read-side evidence."""
    selected = run_id or _latest_run_id(graph)
    # Resolution-aware: Flag props are append-only, so status alone lies once
    # a FlagResolution exists (2026-07-14: the vital read 6 with 1 truly open).
    pending = len(pending_flags(graph))
    sync = _sync(graph, selected)
    degraded = _degraded_feeds(graph, selected)
    infra = infra_projection(graph, azure, settings, now=now, github=github)
    containers = cast("list[dict[str, Any]]", infra["containers"])
    tags = sorted({str(row["image_tag"]) for row in containers if row.get("image")})
    hardware = cast("dict[str, Any]", infra["hardware_cost"])
    llm = cast("dict[str, Any]", infra["llm_cost"])
    hardware_total = hardware.get("total")
    hardware_currency = hardware.get("currency")
    llm_currency = llm["currency"]
    same_currency = hardware_total is not None and hardware_currency == llm_currency
    total = (
        round(
            float(cast("float | int | str", hardware_total)) + float(llm["total"]),
            6,
        )
        if same_currency
        else None
    )
    return {
        "run_id": selected,
        "pending_flags": pending,
        "broker_graph": sync,
        "degraded_feeds": degraded,
        "spine": infra["spine"],
        "bus": infra["bus"],
        "deploy_currency": infra["deploy_currency"],
        "images": {
            "available": bool(tags),
            "tags": tags,
            "container_count": len(containers),
            "status": "observed" if tags else "unavailable",
        },
        "mtd_cost": {
            "status": (
                "tracked"
                if total is not None
                else "split_currency"
                if hardware_total is not None
                else "partial"
            ),
            "currency": llm_currency if same_currency else None,
            "total": total,
            "hardware": hardware_total,
            "hardware_currency": hardware_currency,
            "llm": llm["total"],
            "llm_currency": llm_currency,
            "untracked_llm_models": llm["untracked_models"],
        },
        "next_fire": cast("dict[str, object]", infra["job"])["next_fire"],
    }


def _latest_run_id(graph: GraphStore) -> str:
    rows = list_runs(graph)
    return str(rows[0]["run_id"]) if rows else ""


def _sync(graph: GraphStore, run_id: str) -> dict[str, object]:
    if not run_id:
        return {"status": "unavailable", "rows": 0}
    positions = run_positions(graph, run_id)
    rows = cast("list[dict[str, object]]", positions["rows"])
    if positions["snapshot_at"] is None:
        return {"status": "unavailable", "rows": len(rows)}
    return {
        "status": "in_sync" if all(row["match"] for row in rows) else "diverged",
        "rows": len(rows),
    }


def _degraded_feeds(graph: GraphStore, run_id: str) -> dict[str, object]:
    market = walk_chain(graph, run_id).get("MarketData") if run_id else None
    snapshot = market.props.get("snapshot") if market else None
    quality = snapshot.get("quality") if isinstance(snapshot, Mapping) else None
    notes = quality.get("notes", ()) if isinstance(quality, Mapping) else ()
    names = sorted(
        {name for note in notes if (name := degraded_feed_name(note)) is not None}
    )
    return {"count": len(names), "feeds": names}
