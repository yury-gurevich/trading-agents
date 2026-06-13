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


def all_predictors(graph: GraphStore) -> tuple[PredictorView, ...]:
    """Return all predictors, newest first (by purpose, target, id desc)."""
    views = (_view(node) for node in nodes_by_label(graph, "Predictor"))
    return tuple(
        sorted(
            views,
            key=lambda item: (item.purpose, item.target, item.predictor_id),
            reverse=True,
        )
    )


def _view(node: Node) -> PredictorView:
    return PredictorView(
        predictor_id=str(node.props.get("predictor_id", node.key)),
        purpose=str(node.props.get("purpose", "")),
        target=str(node.props.get("target", "")),
        strategy=str(node.props.get("strategy", "")),
        accuracy=float(node.props.get("accuracy", 0.0)),
        sample_size=int(node.props.get("sample_size", 0)),
        advisory=bool(node.props.get("advisory", True)),
    )
