"""Predictor query projections.

Agent: surfaces
Role: read Predictor nodes and project predictor views, newest first.
External I/O: GraphStore reads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from surfaces.queries._graph import nodes_by_label

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class PredictorView:
    """Operator-facing view of one advisory predictor."""

    predictor_id: str
    purpose: str
    target: str
    strategy: str
    accuracy: float
    sample_size: int
    advisory: bool  # always True this sprint
    promotion_status: str  # advisory | pending_approval | load_bearing


def all_predictors(graph: GraphStore) -> tuple[PredictorView, ...]:
    """Return all predictors, newest first (by purpose, target, id desc)."""
    views = (_view(graph, node) for node in nodes_by_label(graph, "Predictor"))
    return tuple(
        sorted(
            views,
            key=lambda item: (item.purpose, item.target, item.predictor_id),
            reverse=True,
        )
    )


def _view(graph: GraphStore, node: Node) -> PredictorView:
    predictor_id = str(node.props.get("predictor_id", node.key))
    return PredictorView(
        predictor_id=predictor_id,
        purpose=str(node.props.get("purpose", "")),
        target=str(node.props.get("target", "")),
        strategy=str(node.props.get("strategy", "")),
        accuracy=float(node.props.get("accuracy", 0.0)),
        sample_size=int(node.props.get("sample_size", 0)),
        advisory=bool(node.props.get("advisory", True)),
        promotion_status=_promotion_status(graph, predictor_id),
    )


def _promotion_status(graph: GraphStore, predictor_id: str) -> str:
    # Promotion state is graph-derived; key formulas mirror the curator registry
    # (agents/curator/domain/registry.py) and the supervisor flag store. Surfaces
    # read the graph directly and never import an agent module.
    if graph.get_node("PredictorPromotion", f"promotion:{predictor_id}") is not None:
        return "load_bearing"
    subject = f"predictor:{predictor_id}"
    flag = graph.get_node("Flag", f"flag:{subject}:info")
    resolution = graph.get_node("FlagResolution", f"resolution:flag:{subject}:info")
    if flag is not None and resolution is None:
        return "pending_approval"
    return "advisory"
