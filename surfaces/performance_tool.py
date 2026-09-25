"""The "vs the market" tool: the reporter's scoreboard as a chat and MCP answer.

Agent: surfaces
Role: answer whether the book beats the market from the graph alone, never a model.
External I/O: injected GraphStore reads only; no bus request, no LLM (RPT-SEC-02).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from surfaces.dashboard.projections import latest_run_id
from surfaces.queries.performance import run_performance
from surfaces.queries.performance_text import summary

if TYPE_CHECKING:
    from surfaces.context import SurfaceContext

ToolResult = dict[str, object]


def performance_tool(ctx: SurfaceContext, args: ToolResult) -> ToolResult:
    """Return the run's scoreboard numbers and one sentence; default: latest run."""
    raw = args.get("run_id", "")
    if not isinstance(raw, str):
        raise ValueError("run_id must be a string")
    run_id = raw.strip() or latest_run_id(ctx.graph)
    view = run_performance(ctx.graph, run_id)
    result: ToolResult = {
        "run_id": run_id,
        "status": view.status,
        "summary": summary(view),
    }
    if view.status == "measured":
        result["benchmark"] = view.benchmark
        result["metrics"] = dict(view.metrics)
    else:
        result["reason"] = view.reason
    return result
