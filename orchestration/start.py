"""System start: pre-flight checks and the run trigger.

Agent: orchestration
Role: confirm prerequisites before a run, then place the single RunRequest node that
      starts it. The provider polls that node (graph-pull) and ingests; every
      downstream agent then wakes itself off its prerequisite gate, so this is the
      only explicit trigger in the pipeline.
External I/O: none (writes the injected GraphStore).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from contracts.provider import RUN_REQUEST_LABEL

if TYPE_CHECKING:
    from datetime import date

    from kernel import GraphStore, Node


@dataclass(frozen=True)
class PreflightCheck:
    """One named prerequisite outcome shown before a run starts."""

    name: str
    ok: bool
    detail: str


def preflight(
    graph: GraphStore, *, source: object | None, tickers: tuple[str, ...]
) -> tuple[PreflightCheck, ...]:
    """Return the prerequisite checklist for starting a run."""
    return (
        _graph_check(graph),
        PreflightCheck(
            "data source configured",
            source is not None,
            type(source).__name__ if source is not None else "missing",
        ),
        PreflightCheck("universe non-empty", bool(tickers), f"{len(tickers)} tickers"),
    )


def all_passed(checks: tuple[PreflightCheck, ...]) -> bool:
    """Return whether every pre-flight check passed."""
    return all(check.ok for check in checks)


def place_run_request(
    graph: GraphStore,
    *,
    run_id: str,
    tickers: tuple[str, ...],
    as_of: date | None = None,
) -> Node:
    """Write the single RunRequest node that triggers a run (the provider polls it)."""
    requested = as_of or datetime.now(tz=UTC).date()
    return graph.merge_node(
        RUN_REQUEST_LABEL,
        f"run-request:{run_id}",
        {
            "run_id": run_id,
            "tickers": list(tickers),
            "requested_at": requested.isoformat(),
        },
    )


def _graph_check(graph: GraphStore) -> PreflightCheck:
    try:
        graph.list_nodes(RUN_REQUEST_LABEL)
    except Exception as exc:  # any backend failure means the store is unreachable
        return PreflightCheck("graph reachable", False, str(exc))
    return PreflightCheck("graph reachable", True, "ok")
