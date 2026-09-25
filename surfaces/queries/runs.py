"""Graph-pull run read models for the CLI and MCP tools.

Agent: surfaces
Role: summarise graph-pull run chains for the CLI and the MCP `runs` tool.
External I/O: injected GraphStore reads only.

The run list here is the dashboard's run selector too, and each run's stages come
from the shared chain walker, so every surface names the same runs. The earlier model
grouped supervisor `Message` nodes, which on graph-pull runs are operator intents,
never runs (DL-225).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from contracts.provider import RUN_REQUEST_LABEL
from orchestration.batch_chain import CHAIN, walk_chain

if TYPE_CHECKING:
    from kernel import GraphStore, Node

STAGES = tuple(label for _, label in CHAIN)


@dataclass(frozen=True)
class StepRecord:
    """One stage artifact a run's chain reached."""

    name: str
    status: str


@dataclass(frozen=True)
class RunSummary:
    """Surface summary of one graph-pull run."""

    run_id: str
    steps: tuple[StepRecord, ...]
    completed: bool
    headline: str | None


def list_runs(graph: GraphStore) -> list[dict[str, object]]:
    """All known runs, newest first — the run-selector feed."""
    rows: list[dict[str, object]] = [
        {
            "run_id": str(node.props.get("run_id", "")),
            "requested_at": str(node.props.get("requested_at", "")),
        }
        for node in graph.list_nodes(RUN_REQUEST_LABEL)
    ]
    rows.sort(key=lambda r: (str(r["requested_at"]), str(r["run_id"])), reverse=True)
    return rows


def latest_run_id(graph: GraphStore) -> str:
    """The run the dashboard selects when none is named: the one definition."""
    rows = list_runs(graph)
    return str(rows[0]["run_id"]) if rows else ""


def recent_runs(graph: GraphStore, limit: int = 10) -> tuple[RunSummary, ...]:
    """Return the most recent graph-pull runs, newest requested first."""
    return tuple(
        _summary(str(row["run_id"]), walk_chain(graph, str(row["run_id"])))
        for row in list_runs(graph)[: max(limit, 0)]
    )


def run_detail(graph: GraphStore, run_id: str) -> RunSummary | None:
    """Return one run's summary, or None when no RunRequest has that id."""
    chain = walk_chain(graph, run_id) if run_id else {}
    return _summary(run_id, chain) if chain else None


def last_reported_run(graph: GraphStore) -> str | None:
    """Return the newest requested run whose chain reached a Snapshot."""
    for row in list_runs(graph):
        run_id = str(row["run_id"])
        if "Snapshot" in walk_chain(graph, run_id):
            return run_id
    return None


def _summary(run_id: str, chain: dict[str, Node]) -> RunSummary:
    snapshot = chain.get("Snapshot")
    headline = snapshot.props.get("headline_summary") if snapshot else None
    return RunSummary(
        run_id=run_id,
        steps=tuple(StepRecord(label, "done") for label in STAGES if label in chain),
        completed=snapshot is not None,
        headline=headline if isinstance(headline, str) else None,
    )
