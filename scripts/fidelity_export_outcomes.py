"""Downstream outcomes and the benchmark evidence for the S237 fidelity export.

Agent: tooling
Role: project deliberation, execution and fills, and name a benchmark live used but
      never stored.
External I/O: none (reads the injected GraphStore).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING

from scripts.fidelity_export_helpers import node_block, node_props

if TYPE_CHECKING:
    from kernel.graph import GraphStore, Node

_DELIBERATION_PROPS = (
    "verdicts",
    "vetoed_tickers",
    "failed_open_tickers",
    "failed_open_count",
    "real_debate_count",
    "created_at",
)
_BETA = "beta"  # the scanner's feature when a benchmark was present
_RELATIVE_STRENGTH = "rs_score"  # the analyst's metric when a benchmark was present


def deliberation_block(node: Node | None) -> dict[str, object]:
    """Return the verdicts and vetoes, without debate text (DLIB-OUT-02)."""
    return node_block(node, *_DELIBERATION_PROPS)


def execution_block(node: Node | None) -> dict[str, object]:
    """Return the ExecutionRun's counts and posture as stored."""
    return {"key": node.key, **node_props(node)} if node is not None else {}


def fills_for(graph: GraphStore, pm_keys: Iterable[str]) -> list[dict[str, object]]:
    """Return the Fill nodes whose source_run_id names this run's PMRun (R6)."""
    keys = {key for key in pm_keys if key}
    return [
        {"key": node.key, **node_props(node)}
        for node in sorted(graph.list_nodes("Fill"), key=lambda item: item.key)
        if node.props.get("source_run_id") in keys
    ]


def benchmark_gap(
    snapshot: object, scanner: Mapping[str, object], analyst: Mapping[str, object]
) -> bool:
    """Whether live used a benchmark the stored snapshot does not carry (Trap 3)."""
    if not isinstance(snapshot, Mapping) or snapshot.get("benchmark"):
        return False
    return _scanner_used_one(scanner) or _analyst_used_one(analyst)


def _scanner_used_one(scanner: Mapping[str, object]) -> bool:
    candidate_set = _mapping(scanner.get("candidate_set"))
    candidates = _items(candidate_set.get("candidates"))
    traces = (
        _mapping(scanner.get("filter_trace")),
        _mapping(candidate_set.get("filter_trace")),
    )
    verdicts = [item for trace in traces for item in _items(trace.get("verdicts"))]
    return any(_BETA in _mapping(item.get("metrics")) for item in candidates) or any(
        _BETA in _mapping(item.get("features")) for item in verdicts
    )


def _analyst_used_one(analyst: Mapping[str, object]) -> bool:
    recommendation_set = _mapping(analyst.get("recommendation_set"))
    return any(
        _mapping(metric).get("name") == _RELATIVE_STRENGTH
        for item in _items(recommendation_set.get("recommendations"))
        for metric in _items(item.get("quant_metrics"))
    )


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _items(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, Mapping)]
