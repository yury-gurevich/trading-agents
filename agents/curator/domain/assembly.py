"""Training-example assembly by provenance-graph traversal.

Agent: curator
Role: reduce completed TradeNarrative lineage into ordered, labelled example records.
External I/O: GraphStore reads (never writes).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from kernel import GraphStore, Node

NARRATES = "NARRATES"
CLOSES = "CLOSES"
_UNLABELLED = "unlabelled"


@dataclass(frozen=True)
class ExampleRecord:
    """One labelled training example assembled from a TradeNarrative."""

    example_id: str
    content: str
    label: str
    source_ref: str
    metadata: Mapping[str, str]


def assemble_examples(
    graph: GraphStore, *, purpose: str, max_examples: int
) -> tuple[ExampleRecord, ...]:
    """Assemble examples from all TradeNarrative nodes, deterministically ordered."""
    narratives = sorted(graph.list_nodes("TradeNarrative"), key=lambda node: node.key)
    return tuple(
        _record(graph, narrative, purpose) for narrative in narratives[:max_examples]
    )


def _record(graph: GraphStore, narrative: Node, purpose: str) -> ExampleRecord:
    position = _position_for(graph, narrative)
    position_id = str(narrative.props.get("position_id", ""))
    metadata = {
        "run_id": str(narrative.props.get("run_id", "")),
        "position_id": position_id,
    }
    if position is not None and "ticker" in position.props:
        metadata["ticker"] = str(position.props["ticker"])
    return ExampleRecord(
        example_id=f"{purpose}:{position_id}",
        content=str(narrative.props.get("summary", "")),
        label=_label_for(graph, position),
        source_ref=f"TradeNarrative:{narrative.key}",
        metadata=metadata,
    )


def _position_for(graph: GraphStore, narrative: Node) -> Node | None:
    return next(
        iter(graph.descendants(narrative, max_depth=1, edge_types={NARRATES})),
        None,
    )


def _label_for(graph: GraphStore, position: Node | None) -> str:
    if position is None:
        return _UNLABELLED
    close = next(
        iter(graph.ancestors(position, max_depth=1, edge_types={CLOSES})),
        None,
    )
    if close is None:
        return _UNLABELLED
    return str(close.props.get("trigger", _UNLABELLED))
